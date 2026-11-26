"""M7 tests: ATHN behaviour, frozen protocol/config integrity, dev-only selection reproducibility, prior suites.
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m7.py [--out artifacts\\M7\\TEST_RESULTS.json]
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import athn  # noqa: E402
import m7_select as ms  # noqa: E402
import run_baseline as rb  # noqa: E402

A7 = ROOT / "artifacts/M7"


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def test_athn_selftest_and_determinism():
    athn._selftest()
    import cv2
    img = cv2.cvtColor(cv2.imread(str(ROOT / "data/benchmarks/syn_cheques/SYN_0001_num.png")), cv2.COLOR_BGR2RGB)
    cfg = load("artifacts/M7/configs/P1-A.json")
    a, ma = athn.apply(img, cfg)
    b, mb = athn.apply(img.copy(), cfg)
    assert np.array_equal(a, b) and ma == mb and ma["applied"] and a.shape[0] <= 256 and a.shape[1] <= 1024


def test_protocol_and_frozen_config_integrity():
    assert (A7 / "PROTOCOL_FROZEN.sha256").read_text().split()[0] == sha("artifacts/M7/SELECTION_PROTOCOL.md")
    fz = load("artifacts/M7/FROZEN_CONFIG.json")
    assert fz["selected"] == "P1-A" and fz["method_config"] == load(fz["method_config_file"])
    assert fz["method_config_sha256"] == sha(fz["method_config_file"])
    changed = [p for p, h in fz["source_sha256"].items() if sha(p) != h]
    assert not changed, changed
    assert load("artifacts/M8/configs/proposed_P1-A.json") == fz["method_config"]


def test_selection_reproducible_from_saved_runs():
    dev = load("artifacts/M7/DEVELOPMENT_RESULTS.json")
    b0 = ms.summary(ROOT / "artifacts/M5_DEV")
    for c in ms.CANDIDATES + ms.ABLATIONS:
        s = ms.summary(A7 / "dev" / c)
        checks, ok = ms.guardrails(s, b0)
        assert ok == dev["results"][c]["passes"] and s["D6_num"] == dev["results"][c]["D6_num"], c
    assert dev["selected"] == "P1-A" and dev["success_rule_met"] and dev["passing_candidates"] == ["P1-A", "P1-C"]


def test_m7_runs_are_dev_only_and_complete():
    for c in ms.CANDIDATES + ms.ABLATIONS:
        res = load(f"artifacts/M7/dev/{c}/BASELINE_RESULTS.json")
        assert res["run"]["errors"] == 0 and res["run"]["entries"] == 251
        assert {r["split"] for r in res["results"]} == {"dev"}


def test_identity_path_reuses_baseline_predictions():
    m5 = {r["id"]: r for r in load("artifacts/M5_DEV/BASELINE_RESULTS.json")["results"]}
    rows = load("artifacts/M7/dev/P1-A/BASELINE_RESULTS.json")["results"]
    ident = [r for r in rows if not r["preprocess"].get("applied") and r["prediction"] is not None]
    assert len(ident) == 251 - 115 - sum(1 for r in rows if not r["recognition_eligible"] and not r["preprocess"].get("applied")
                                         and r["prediction"] is None)
    for r in ident:
        assert r["cache_key"] == rb.cache_key(r["input_sha256"]) and r["prediction"] == m5[r["id"]]["prediction"], r["id"]


def test_run_method_refuses_test_split_without_flag():
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "scripts/run_method.py"), "--split", "test",
                            "--config", str(A7 / "configs/P1-A.json"), "--out-dir", d, "--cache", str(Path(d) / "c.jsonl")],
                           capture_output=True, text=True)
        assert r.returncode == 2 and "authorize-test-split" in r.stderr and not (Path(d) / "BASELINE_RESULTS.json").exists()


def test_preprocess_path_equals_array_path():
    import smoke_inference as si
    sys.path.insert(0, str(si.UPSTREAM))
    si.install_vocab(rb.DICT)  # same adapter the runners use before importing the upstream dataset module
    from PIL import Image
    p = ROOT / "data/benchmarks/syn_cheques/SYN_0001_words.png"
    x1, m1 = si.preprocess(p)
    x2, m2 = si.preprocess_array(np.array(Image.open(p).convert("RGB")))
    assert x1.equal(x2) and m1.equal(m2)


def test_p2_decision_follows_rule():
    p2 = load("artifacts/M7/dev/P2/P2_RESULTS.json")
    a, b = p2["p1_full_line"], p2["p2_segmented"]
    assert p2["adopt_p2"] == (b["value_correct"] - a["value_correct"] >= 3 and b["cer"] < a["cer"]) and not p2["adopt_p2"]
    assert a["n"] == b["n"] == 37


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
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tests/test_m6.py")], capture_output=True, text=True)
    results.append({"test": "m6_m5_m4_suites", "status": "passed" if r.returncode == 0 else "failed",
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
