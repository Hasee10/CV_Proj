"""M5 baseline inference: unchanged LoGo-HTR on the frozen manifests (dev split only unless explicitly authorised).

- Verifies the frozen manifest hashes (artifacts/M4_FINAL/SUMMARY.json) and, via smoke_inference.load_model, the
  checkpoint hash. Only the image is passed to the model; labels are joined to predictions afterwards.
- One inference per unique image: results are cached in <out-dir>/prediction_cache.jsonl, keyed by
  sha256(image) + checkpoint sha256 + preprocessing + decoding configuration, appended as they are computed.
- --pilot N: the first N dev entries per dataset by sorted id (a fixed rule, no performance-based choice).
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\run_baseline.py --out-dir artifacts\\M5_DEV [--pilot 5]
"""
import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import smoke_inference as si  # noqa: E402

MANIFESTS = {"D1": "data/public/gnhk/subset/manifest.json", "D4": "data/benchmarks/cvl_numeric/manifest.json",
             "D5": "data/benchmarks/gnhk_pairs/manifest.json", "D6": "data/benchmarks/syn_cheques/manifest.json"}
PREPROC = "upstream test transform: PIL RGB, ScaleToLimitRange(w 16-1024, h 16-256), ToTensor, batch 1, no padding"
DECODE = "upstream bidirectional beam search: beam 10, max_len 200, alpha 1.0, temperature 1.0, early_stopping False"
DICT = "SSL_HWD_Dict.txt"


def cache_key(img_sha: str) -> str:
    return hashlib.sha256(f"{img_sha}|{si.CKPT_SHA256}|{PREPROC}|{DECODE}|{DICT}".encode()).hexdigest()


def load_entries(split):
    frozen = json.loads((ROOT / "artifacts/M4_FINAL/SUMMARY.json").read_text(encoding="utf-8"))["frozen_manifests_sha256"]
    entries = []
    for ds, rel in MANIFESTS.items():
        raw = (ROOT / rel).read_bytes()
        if hashlib.sha256(raw).hexdigest() != frozen[rel]:
            raise SystemExit(f"manifest {rel} differs from the frozen M4-FINAL hash")
        for s in json.loads(raw)["samples"]:
            if s["split"] == split:
                entries.append({**s, "dataset": ds})
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--pilot", type=int)
    ap.add_argument("--authorize-test-split", action="store_true", help="required for the locked test split")
    a = ap.parse_args()
    if a.split != "dev" and not a.authorize_test_split:
        print("ERROR: locked test split requires --authorize-test-split", file=sys.stderr)
        return 2
    if not sys.flags.utf8_mode:
        print("ERROR: run with python -X utf8", file=sys.stderr)
        return 2
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tag = f"pilot{a.pilot}" if a.pilot else "full"
    res_path = out / f"BASELINE_RESULTS_{tag}.json" if a.pilot else out / "BASELINE_RESULTS.json"
    if res_path.exists():
        print(f"ERROR: {res_path} exists; refusing to overwrite", file=sys.stderr)
        return 2
    entries = sorted(load_entries(a.split), key=lambda s: (s["dataset"], s["id"]))
    if a.pilot:
        entries = [e for ds in MANIFESTS for e in [x for x in entries if x["dataset"] == ds][:a.pilot]]
    cache_path = out / "prediction_cache.jsonl"
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            cache[r["key"]] = r
    unique = {}
    for e in entries:
        unique.setdefault(e["sha256"], e)

    import torch
    sys.path.insert(0, str(si.UPSTREAM))
    vmod = si.install_vocab(DICT)
    vocab = vmod.vocab
    report = {"torch": torch.__version__, "threads": torch.get_num_threads(), "python": sys.version.split()[0]}
    todo = [e for h, e in unique.items() if cache_key(h) not in cache]
    computed = set()
    t_all = time.perf_counter()
    if todo:
        t0 = time.perf_counter()
        model = si.load_model(report)
        report["model_load_seconds"] = round(time.perf_counter() - t0, 3)
        with torch.inference_mode(), open(cache_path, "a", encoding="utf-8") as cf:
            warm = next((e for e in todo if not si.readable(ROOT / e["file"], e["sha256"])), None)
            if warm:
                x, m = si.preprocess(ROOT / warm["file"])
                t0 = time.perf_counter()
                model.approximate_joint_search(x, m)
                report["warmup_seconds"] = round(time.perf_counter() - t0, 4)
            for i, e in enumerate(todo, 1):
                rec = {"key": cache_key(e["sha256"]), "image_sha256": e["sha256"], "checkpoint_sha256": si.CKPT_SHA256,
                       "preprocessing": PREPROC, "decoding": DECODE, "dictionary": DICT, "error": None,
                       "prediction": None, "raw_token_ids": None, "score": None, "latency_seconds": None,
                       "input_shape": None, "first_file": e["file"]}
                err = si.readable(ROOT / e["file"], e["sha256"])
                if err:
                    rec["error"] = err
                else:
                    try:
                        t0 = time.perf_counter()
                        x, m = si.preprocess(ROOT / e["file"])
                        hyp = model.approximate_joint_search(x, m)[0]
                        rec["latency_seconds"] = round(time.perf_counter() - t0, 4)
                        rec.update(prediction="".join(vocab.indices2words(hyp.seq)), raw_token_ids=hyp.seq,
                                   score=float(hyp.score), input_shape=list(x.shape))
                    except Exception as ex:
                        rec["error"] = f"{type(ex).__name__}: {ex}"
                cf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                cf.flush()
                cache[rec["key"]] = rec
                computed.add(rec["key"])
                if i % 25 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} inferred", flush=True)
    rows, seen = [], set()
    for e in entries:
        k = cache_key(e["sha256"])
        c = cache[k]
        status = "computed_this_run" if k in computed and k not in seen else ("dedup_same_image" if k in seen else "reused_cache")
        seen.add(k)
        rows.append({"id": e["id"], "dataset": e["dataset"], "split": e["split"], "category": e["category"],
                     "template": e.get("template"), "stratum": e.get("stratum"), "genuine": e.get("genuine_handwriting", True),
                     "input_sha256": e["sha256"], "ground_truth": e["ground_truth"], "gt_value": e.get("gt_value"),
                     "recognition_eligible": bool(e["ground_truth"]), "prediction": c["prediction"],
                     "raw_token_ids": c["raw_token_ids"], "score": c["score"], "error": c["error"],
                     "latency_seconds": c["latency_seconds"], "input_shape": c["input_shape"], "cache_status": status,
                     "cache_key": k})
    lat = [cache[k]["latency_seconds"] for k in computed if cache[k]["latency_seconds"] is not None]
    report.update({"split": a.split, "mode": tag, "entries": len(rows), "unique_inputs": len(unique),
                   "computed_this_run": len(computed), "reused_from_cache": len(unique) - len(computed),
                   "wall_seconds": round(time.perf_counter() - t_all, 2),
                   "inference_seconds_computed": round(sum(lat), 2),
                   "median_latency_computed": statistics.median(lat) if lat else None,
                   "checkpoint_sha256": si.CKPT_SHA256, "preprocessing": PREPROC, "decoding": DECODE, "dictionary": DICT,
                   "manifests": MANIFESTS})
    res_path.write_text(json.dumps({"run": report, "results": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if not any(r["error"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
