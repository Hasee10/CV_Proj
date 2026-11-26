"""Cached, resumable baseline inference over any manifest(s) of image entries (dev-only guard).

Same unchanged configuration and cache key as scripts/run_baseline.py (image sha256 + checkpoint + preprocessing +
decoding + dictionary). Predictions are appended to --cache as they are computed, so an interrupted run resumes.
Only images are passed to the model. Entries must carry id, file, sha256 and split; any split other than dev is refused.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\run_inference_set.py --manifest M.json [--manifest M2.json]
       --cache data\\stress\\m6_cache.jsonl --out artifacts\\M6\\X.json [--limit-ids ids.json]
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_baseline as rb  # noqa: E402
import smoke_inference as si  # noqa: E402


def load_cache(path: Path) -> dict:
    cache = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[r["key"]] = r
    return cache


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", action="append", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit-ids", help="JSON list of entry ids to run (fixed subsets such as the pilot)")
    a = ap.parse_args()
    if not sys.flags.utf8_mode:
        print("ERROR: run with python -X utf8", file=sys.stderr)
        return 2
    out = Path(a.out)
    if out.exists():
        print(f"ERROR: {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    entries = [s for m in a.manifest for s in json.loads(Path(m).read_text(encoding="utf-8"))["samples"]]
    if a.limit_ids:
        keep = set(json.loads(Path(a.limit_ids).read_text(encoding="utf-8")))
        entries = [e for e in entries if e["id"] in keep]
    bad = [e["id"] for e in entries if e.get("split") != "dev"]
    if bad:
        print(f"ERROR: non-dev entries refused: {bad[:5]}", file=sys.stderr)
        return 2
    cache_path = Path(a.cache)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = load_cache(cache_path)
    unique = {}
    for e in entries:
        unique.setdefault(e["sha256"], e)
    todo = [e for h, e in unique.items() if rb.cache_key(h) not in cache]
    computed, report = set(), {}
    t_all = time.perf_counter()
    if todo:
        import torch
        sys.path.insert(0, str(si.UPSTREAM))
        vocab = si.install_vocab(rb.DICT).vocab
        model = si.load_model(report)
        with torch.inference_mode(), open(cache_path, "a", encoding="utf-8") as cf:
            warm = next((e for e in todo if not si.readable(ROOT / e["file"], e["sha256"])), None)
            if warm:
                x, m = si.preprocess(ROOT / warm["file"])
                model.approximate_joint_search(x, m)
            for i, e in enumerate(todo, 1):
                rec = {"key": rb.cache_key(e["sha256"]), "image_sha256": e["sha256"], "checkpoint_sha256": si.CKPT_SHA256,
                       "preprocessing": rb.PREPROC, "decoding": rb.DECODE, "dictionary": rb.DICT, "error": None,
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
                if i % 100 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} inferred ({time.perf_counter() - t_all:.0f} s)", flush=True)
    rows = []
    for e in entries:
        c = cache[rb.cache_key(e["sha256"])]
        rows.append({k: e.get(k) for k in ("id", "parent_id", "corruption", "level", "dataset", "category", "condition",
                                           "ground_truth", "gt_value", "group_id", "template")}
                    | {"input_sha256": e["sha256"], "prediction": c["prediction"], "raw_token_ids": c["raw_token_ids"],
                       "error": c["error"], "latency_seconds": c["latency_seconds"], "input_shape": c["input_shape"],
                       "cache_status": "computed_this_run" if c["key"] in computed else "reused_cache"})
    lat = [cache[k]["latency_seconds"] for k in computed if cache[k]["latency_seconds"] is not None]
    run = {"entries": len(rows), "unique_inputs": len(unique), "computed_this_run": len(computed),
           "reused": len(unique) - len(computed), "wall_seconds": round(time.perf_counter() - t_all, 2),
           "inference_seconds": round(sum(lat), 2), "median_latency": statistics.median(lat) if lat else None,
           "errors": sum(1 for r in rows if r["error"]), "manifests": a.manifest, "checkpoint_sha256": si.CKPT_SHA256,
           "model_load": report.get("missing_keys") == [] and report.get("unexpected_keys") == [] if todo else "not loaded (all cached)"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"run": run, "results": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(run, indent=1))
    return 0 if not run["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
