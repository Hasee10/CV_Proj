"""M8 tests: locked-test accounting, identical inputs, frozen config, reproducible comparison, figures, prior suites.
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m8.py [--out artifacts\\M8\\TEST_RESULTS.json]
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
import m8_compare as mc  # noqa: E402
import run_baseline as rb  # noqa: E402

A8 = ROOT / "artifacts/M8"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def test_counts_match_frozen_manifests():
    ents = rb.load_entries("test")
    assert len(ents) == 621 and sum(1 for e in ents if e["ground_truth"]) == 603
    for m in ("baseline", "proposed"):
        res = load(f"artifacts/M8/runs/{m}/BASELINE_RESULTS.json")
        assert res["run"]["entries"] == 621 and res["run"]["errors"] == 0 and res["run"]["split"] == "test"
        assert sorted(r["id"] for r in res["results"]) == sorted(e["id"] for e in ents)
        pr = load(f"artifacts/M8/runs/{m}/PAIR_RESULTS.json")["pairs"]
        assert len(pr) == 216 and Counter(p["dataset"] for p in pr) == {"syn_cheques": 164, "gnhk_pairs": 52}


def test_identical_inputs_and_frozen_config():
    b, p = (load(f"artifacts/M8/runs/{m}/BASELINE_RESULTS.json") for m in ("baseline", "proposed"))
    assert {r["id"]: r["input_sha256"] for r in b["results"]} == {r["id"]: r["input_sha256"] for r in p["results"]}
    fz = load("artifacts/M7/FROZEN_CONFIG.json")
    assert p["run"]["config"] == fz["method_config"] and b["run"]["config"]["method"] == "baseline"
    assert hashlib.sha256((ROOT / fz["method_config_file"]).read_bytes()).hexdigest() == fz["method_config_sha256"]


def test_identity_rows_agree_between_methods():
    b = {r["id"]: r for r in load("artifacts/M8/runs/baseline/BASELINE_RESULTS.json")["results"]}
    for r in load("artifacts/M8/runs/proposed/BASELINE_RESULTS.json")["results"]:
        if not r["preprocess"].get("applied"):
            assert r["prediction"] == b[r["id"]]["prediction"], r["id"]


def test_comparison_matches_scored_metrics():
    cm = load("artifacts/M8/COMPARATIVE_METRICS.json")
    for m in ("baseline", "proposed"):
        g = load(f"artifacts/M8/runs/{m}/METRICS.json")["groups"]
        for k, row in cm["datasets"].items():
            assert row["exact"][m] == g[k]["primary_failure_aware"]["exact"]
            assert abs(row["cer"][m] - g[k]["primary_failure_aware"]["cer"]) < 1e-4


def test_paired_statistics_recomputable():
    st = load("artifacts/M8/STATISTICAL_ANALYSIS.json")["results"]
    b = {r["id"]: r for r in load("artifacts/M8/runs/baseline/BASELINE_RESULTS.json")["results"]}
    p = {r["id"]: r for r in load("artifacts/M8/runs/proposed/BASELINE_RESULTS.json")["results"]}
    for g in mc.GROUPS.values():
        ids = [i for i in b if b[i]["recognition_eligible"] and mc.gkey(b[i]) == g]
        ib, ip = [mc.item(b[i]) for i in ids], [mc.item(p[i]) for i in ids]
        n = sum(x["n"] for x in ib)
        assert abs((sum(x["ed"] for x in ip) - sum(x["ed"] for x in ib)) / n - st[g]["cer_delta"]) < 1e-4
        assert st[g]["exact_mcnemar"]["improved"] - st[g]["exact_mcnemar"]["regressed"] == st[g]["exact_delta"]
    assert mc.mcnemar(0, 0) == 1.0 and abs(mc.mcnemar(0, 6) - 0.03125) < 1e-9


def test_figures_exist_and_are_newer_than_results():
    need = ["test_cer_exact.png", "test_cer_delta_ci.png", "test_pair_decisions.png", "test_latency.png"]
    src = (A8 / "COMPARATIVE_METRICS.json").stat().st_mtime
    for f in need:
        assert (A8 / "figures" / f).stat().st_mtime >= src - 5, f


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
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tests/test_m7.py")], capture_output=True, text=True)
    results.append({"test": "m7_m6_m5_m4_suites", "status": "passed" if r.returncode == 0 else "failed",
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
