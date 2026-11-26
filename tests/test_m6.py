"""M6 tests: stress accounting and lineage, dev-only, reproducible metrics, diagnostics coverage, figures, prior suites.
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m6.py [--out artifacts\\M6\\TEST_RESULTS.json]
"""
import hashlib
import json
import subprocess
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import m6_analyze as ma  # noqa: E402
import run_baseline as rb  # noqa: E402

A6 = ROOT / "artifacts/M6"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def test_every_planned_variant_accounted_with_lineage():
    parents = {p["id"]: p for p in load("data/stress/m6_parents.json")["samples"]}
    variants = load("data/stress/m6_dev/manifest.json")["samples"]
    assert len(parents) == 245 and len(variants) == 3675
    per = Counter(v["parent_id"] for v in variants)
    assert set(per) == set(parents) and set(per.values()) == {15}
    assert len({(v["parent_id"], v["corruption"], v["level"]) for v in variants}) == 3675
    for v in variants:
        p = parents[v["parent_id"]]
        assert v["split"] == p["split"] == "dev" and v["parent_sha256"] == p["sha256"] and v["ground_truth"] == p["ground_truth"]
        assert hashlib.sha256((ROOT / v["file"]).read_bytes()).hexdigest() == v["sha256"]


def test_stress_results_complete_dev_only_and_mapped():
    res = load("artifacts/M6/STRESS_RESULTS.json")
    vm = {v["id"]: v for v in load("data/stress/m6_dev/manifest.json")["samples"]}
    rows = res["results"]
    assert len(rows) == 3675 and {r["id"] for r in rows} == set(vm)
    assert all((r["prediction"] is not None) or r["error"] for r in rows)
    assert all(r["input_sha256"] == vm[r["id"]]["sha256"] for r in rows)
    test_ids = {e["id"] for e in rb.load_entries("test")}
    assert not test_ids & {r["parent_id"] for r in rows}
    cache = {json.loads(l)["key"]: json.loads(l) for l in (ROOT / "data/stress/m6_cache.jsonl").read_text(encoding="utf-8").splitlines()}
    for r in rows[:200]:
        c = cache[rb.cache_key(r["input_sha256"])]
        assert c["prediction"] == r["prediction"] and c["raw_token_ids"] == r["raw_token_ids"]


def test_stress_metrics_reproducible_and_paired():
    saved = load("artifacts/M6/STRESS_METRICS.json")["groups"]
    clean = [r for r in load("artifacts/M5_DEV/BASELINE_RESULTS.json")["results"] if r["recognition_eligible"]]
    stress = load("artifacts/M6/STRESS_RESULTS.json")["results"]
    cmap = {r["id"]: r for r in clean}
    for g, c, lv in (("D1", "blur", 3), ("D4", "noise", 2), ("D6_words_SYN", "lowres", 1)):
        var = [r for r in stress if r["corruption"] == c and r["level"] == lv and ma.group_of(cmap[r["parent_id"]]) == g]
        again = ma.summarize(var)
        cell = saved[g][f"{c}_s{lv}"]
        assert again["cer"] == cell["cer"] and again["exact"] == cell["exact"] and again["n"] == cell["n"]
        assert cell["n"] == saved[g]["clean"]["n"]  # paired: same parents as the clean group
        assert cell["paired_clean_cer"] == ma.summarize([cmap[r["parent_id"]] for r in var])["cer"]


def test_diagnostics_complete_and_oracle_geometry():
    dm = load("data/diagnostics/m6/manifest.json")["samples"] + load("data/diagnostics/m6/dxc_oracle_manifest.json")["samples"]
    raw = load("artifacts/M6/DIAGNOSTIC_RAW.json")["results"]
    assert {r["id"] for r in raw} == {d["id"] for d in dm} and all(r.get("prediction") is not None or r["error"] for r in raw)
    oracle = [d for d in dm if d["condition"].startswith("DXC_oracle1x")]
    by = Counter(d["parent_id"] for d in oracle)
    assert all(by[p] == len(next(d for d in oracle if d["parent_id"] == p)["ground_truth"].split()) for p in by)
    res = load("artifacts/M6/DIAGNOSTIC_RESULTS.json")
    assert set(res) >= {"DX-A", "DX-B", "DX-C", "DX-D", "DX-E"}


def test_figures_derived_from_saved_results():
    figs = sorted(p.name for p in (A6 / "figures").glob("*.png"))
    need = {"cer_vs_severity.png", "exact_vs_severity.png", "degradation_heatmap.png", "error_vs_geometry.png",
            "error_categories.png", "diagnostics.png", "examples_largest_paired_errors.png"}
    assert need <= set(figs), figs
    newest_input = max((A6 / f).stat().st_mtime for f in ("STRESS_METRICS.json", "DIAGNOSTIC_RESULTS.json"))
    assert all((A6 / "figures" / f).stat().st_mtime >= newest_input - 5 for f in need)


def test_protocol_amendments_recorded():
    txt = (A6 / "EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")
    assert "Amendment A1" in txt and "Amendment A2" in txt
    assert (A6 / "PROTOCOL_FROZEN.sha256").exists()


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out and Path(out).exists():
        print(f"ERROR: {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    results = []
    for name, fn in [(k, v) for k, v in globals().items() if k.startswith("test_") and callable(v)]:
        t0 = time.perf_counter()
        try:
            fn()
            results.append({"test": name, "status": "passed", "seconds": round(time.perf_counter() - t0, 3)})
        except Exception as e:
            results.append({"test": name, "status": "failed", "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]})
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tests/test_m5_dev.py")], capture_output=True, text=True)
    results.append({"test": "m5_dev_and_m4_suites", "status": "passed" if r.returncode == 0 else "failed",
                    "detail": r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]})
    summary = {"total": len(results), "passed": sum(x["status"] == "passed" for x in results),
               "failed": sum(x["status"] == "failed" for x in results), "results": results}
    for x in results:
        print(f"{x['status']:6} {x['test']} {x.get('error', x.get('detail', ''))}")
    print(f"{summary['passed']}/{summary['total']} passed")
    if out:
        Path(out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
