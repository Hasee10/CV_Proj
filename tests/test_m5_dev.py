"""M5-DEV sanity tests for the baseline orchestration (reads saved results; re-infers 3 fixed dev samples).
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m5_dev.py [--out artifacts\\M5_DEV\\TEST_RESULTS.json]
"""
import hashlib
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eval_metrics as em  # noqa: E402
import run_baseline as rb  # noqa: E402
import score_baseline as sb  # noqa: E402
import smoke_inference as si  # noqa: E402

D = ROOT / "artifacts/M5_DEV"
RES = json.loads((D / "BASELINE_RESULTS.json").read_text(encoding="utf-8"))
ROWS = RES["results"]


def test_every_dev_entry_once_and_no_test_samples():
    expected = rb.load_entries("dev")  # also re-checks frozen manifest hashes
    assert sorted(e["id"] for e in expected) == sorted(r["id"] for r in ROWS)
    assert all(r["split"] == "dev" for r in ROWS)
    assert all((r["prediction"] is not None) or r["error"] for r in ROWS)
    test_ids = {e["id"] for e in rb.load_entries("test")}
    assert not test_ids & {r["id"] for r in ROWS}


def test_input_hashes_and_checkpoint():
    man = {e["id"]: e for e in rb.load_entries("dev")}
    for r in ROWS:
        assert r["input_sha256"] == man[r["id"]]["sha256"]
        assert hashlib.sha256((ROOT / man[r["id"]]["file"]).read_bytes()).hexdigest() == r["input_sha256"]
    cache = [json.loads(l) for l in (D / "prediction_cache.jsonl").read_text(encoding="utf-8").splitlines()]
    assert {c["checkpoint_sha256"] for c in cache} == {si.CKPT_SHA256}
    assert len({c["key"] for c in cache}) == len(cache) == len({r["input_sha256"] for r in ROWS})
    assert hashlib.sha256((ROOT / "models/logo_htr/Downstream_Full_Model_Best.ckpt").read_bytes()).hexdigest() == si.CKPT_SHA256


def test_metrics_reproducible_from_saved_predictions():
    saved = json.loads((D / "METRICS.json").read_text(encoding="utf-8"))["groups"]
    for name, sel in (("D1_gnhk_words_genuine", lambda r: r["dataset"] == "D1"),
                      ("D4_cvl_numeric_genuine", lambda r: r["dataset"] == "D4"),
                      ("D6_syn_words_SYNTHETIC", lambda r: r["category"] == "syn_words")):
        again = json.loads(json.dumps(sb.group_metrics([r for r in ROWS if sel(r)]), default=str))
        assert again == saved[name], name


def test_pairs_map_to_field_predictions():
    by = {r["id"]: r for r in ROWS}
    pr = json.loads((D / "PAIR_RESULTS.json").read_text(encoding="utf-8"))["pairs"]
    dev_pairs = [p for p in json.loads((ROOT / "data/benchmarks/amount_pairs.json").read_text(encoding="utf-8"))["pairs"] if p["split"] == "dev"]
    assert sorted(p["pair_id"] for p in pr) == sorted(p["pair_id"] for p in dev_pairs)
    for p in pr:
        n, w = by[p["num_id"]], by[p["words_id"]]
        assert p["num_prediction"] == n["prediction"] and p["words_prediction"] == w["prediction"]
        assert p["decision"] == em.decide(sb.value_of(n), sb.value_of(w))


def test_ground_truth_not_passed_to_recognition():
    src = (ROOT / "scripts/run_baseline.py").read_text(encoding="utf-8")
    loop = src[src.index("for i, e in enumerate(todo"):src.index("rows, seen = [], set()")]
    assert "ground_truth" not in loop and "gt_value" not in loop and "si.preprocess(ROOT / e[\"file\"])" in loop


def test_test_split_refused_without_authorisation():
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "scripts/run_baseline.py"), "--out-dir",
                        str(D / "_refuse_check"), "--split", "test"], capture_output=True, text=True)
    assert r.returncode == 2 and "authorize" in r.stderr and not (D / "_refuse_check").exists()


def test_fresh_reinference_matches_cache():
    import torch
    sys.path.insert(0, str(si.UPSTREAM))
    vmod = si.install_vocab(rb.DICT)
    model = si.load_model({})
    picks = [next(r for r in ROWS if r["dataset"] == ds and r["recognition_eligible"]) for ds in ("D1", "D4", "D6")]
    man = {e["id"]: e for e in rb.load_entries("dev")}
    with torch.inference_mode():
        for r in picks:
            x, m = si.preprocess(ROOT / man[r["id"]]["file"])
            hyp = model.approximate_joint_search(x, m)[0]
            assert hyp.seq == r["raw_token_ids"], r["id"]
            assert "".join(vmod.vocab.indices2words(hyp.seq)) == r["prediction"]


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
            results.append({"test": name, "status": "failed", "seconds": round(time.perf_counter() - t0, 3),
                            "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]})
    # regression suites from M4 (online suite also runs the 27-test audit suite)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tests/test_m4_online.py")], capture_output=True, text=True)
    results.append({"test": "m4_online_and_audit_suites", "status": "passed" if r.returncode == 0 else "failed",
                    "detail": r.stdout.strip().splitlines()[-1]})
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
