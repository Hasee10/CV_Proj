"""Run a recognition method (baseline, uniform resize or ATHN) on a frozen split; cached and resumable.

Output rows use the M5 BASELINE_RESULTS format (so scripts/score_baseline.py scores them) plus preprocessing metadata.
Cache key: unchanged images reuse the M5 key (image sha256 + checkpoint + config); transformed images are keyed by the
sha256 of the transformed pixels + shape + the same model configuration. The test split needs --authorize-test-split.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\run_method.py --split dev --config CFG.json --out-dir DIR --cache C.jsonl
CFG: {"id": "P1-A", "method": "athn"|"uniform"|"baseline", ...athn params | "scale": 2.0}
"""
import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import athn  # noqa: E402
import run_baseline as rb  # noqa: E402
import smoke_inference as si  # noqa: E402


def transform(rgb, cfg):
    if cfg["method"] == "baseline":
        return rgb, {"method": "baseline", "applied": False, "path": "identity"}
    if cfg["method"] == "uniform":
        s = cfg["scale"]
        out = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
        return out, {"method": "uniform", "applied": True, "scale": s, "interpolation": "INTER_CUBIC", "path": "resized"}
    return athn.apply(rgb, cfg)


def key_for(entry_sha, img, meta):
    if not meta.get("applied"):
        return rb.cache_key(entry_sha)
    h = hashlib.sha256(img.tobytes() + str(img.shape).encode()).hexdigest()
    return rb.cache_key("pixels:" + h)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--authorize-test-split", action="store_true")
    a = ap.parse_args()
    if a.split != "dev" and not a.authorize_test_split:
        print("ERROR: locked test split requires --authorize-test-split", file=sys.stderr)
        return 2
    if not sys.flags.utf8_mode:
        print("ERROR: run with python -X utf8", file=sys.stderr)
        return 2
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    out = Path(a.out_dir)
    res_path = out / "BASELINE_RESULTS.json"   # scorer input name; the directory identifies the method
    if res_path.exists():
        print(f"ERROR: {res_path} exists; refusing to overwrite", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    entries = sorted(rb.load_entries(a.split), key=lambda s: (s["dataset"], s["id"]))
    cache_path = Path(a.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[r["key"]] = r
    model = vocab = None
    rows, computed, t_all = [], 0, time.perf_counter()
    import torch
    with open(cache_path, "a", encoding="utf-8") as cf:
        for i, e in enumerate(entries, 1):
            err = si.readable(ROOT / e["file"], e["sha256"])
            img, meta = None, {}
            if not err:
                rgb = cv2.cvtColor(cv2.imread(str(ROOT / e["file"])), cv2.COLOR_BGR2RGB)
                t0 = time.perf_counter()
                img, meta = transform(rgb, cfg)
                meta["preprocess_seconds"] = round(time.perf_counter() - t0, 4)
            k = key_for(e["sha256"], img, meta) if img is not None else None
            rec = cache.get(k) if k else None
            status = "reused_cache"
            if rec is None:
                rec = {"key": k, "image_sha256": e["sha256"], "error": err, "prediction": None, "raw_token_ids": None,
                       "score": None, "latency_seconds": None, "input_shape": None, "config_id": cfg["id"]}
                if not err:
                    if model is None:
                        sys.path.insert(0, str(si.UPSTREAM))
                        vocab = si.install_vocab(rb.DICT).vocab
                        model = si.load_model({})
                    try:
                        with torch.inference_mode():
                            t0 = time.perf_counter()
                            x, m = si.preprocess_array(img)
                            hyp = model.approximate_joint_search(x, m)[0]
                            rec["latency_seconds"] = round(time.perf_counter() - t0, 4)
                        rec.update(prediction="".join(vocab.indices2words(hyp.seq)), raw_token_ids=hyp.seq,
                                   score=float(hyp.score), input_shape=list(x.shape))
                    except Exception as ex:
                        rec["error"] = f"{type(ex).__name__}: {ex}"
                if k:
                    cf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    cf.flush()
                    cache[k] = rec
                computed += 1
                status = "computed_this_run"
            rows.append({"id": e["id"], "dataset": e["dataset"], "split": e["split"], "category": e["category"],
                         "template": e.get("template"), "stratum": e.get("stratum"), "genuine": e.get("genuine_handwriting", True),
                         "group_id": e.get("group_id"), "input_sha256": e["sha256"], "ground_truth": e["ground_truth"],
                         "gt_value": e.get("gt_value"), "recognition_eligible": bool(e["ground_truth"]),
                         "prediction": rec["prediction"], "raw_token_ids": rec["raw_token_ids"], "score": rec["score"],
                         "error": rec["error"], "latency_seconds": rec["latency_seconds"], "input_shape": rec["input_shape"],
                         "cache_status": status, "cache_key": k, "preprocess": meta})
            if i % 100 == 0:
                print(f"  {i}/{len(entries)} ({time.perf_counter() - t_all:.0f} s)", flush=True)
    lat = [r["latency_seconds"] for r in rows if r["latency_seconds"] is not None]
    run = {"config": cfg, "split": a.split, "entries": len(rows), "computed_this_run": computed,
           "errors": sum(1 for r in rows if r["error"]), "wall_seconds": round(time.perf_counter() - t_all, 2),
           "median_latency": statistics.median(lat) if lat else None, "checkpoint_sha256": si.CKPT_SHA256,
           "resized": sum(1 for r in rows if r["preprocess"].get("applied"))}
    res_path.write_text(json.dumps({"run": run, "results": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(run))
    return 0 if not run["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
