"""M7 P2 check (frozen protocol): chosen P1 + M6 A2 word segmentation on D6 written-amount dev crops only.
Each segmented word is ATHN-normalised and recognised separately; predictions are joined with single spaces.
Compared with the chosen P1 full-line run on the same crops. Usage:
  .venv\\Scripts\\python.exe -X utf8 -I scripts\\m7_p2.py --p1 P1-A
"""
import argparse
import hashlib
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import athn  # noqa: E402
import eval_metrics as em  # noqa: E402
import m6_prepare as m6  # noqa: E402
import run_baseline as rb  # noqa: E402
import smoke_inference as si  # noqa: E402

CACHE = ROOT / "data/m7/cache.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p1", required=True)
    a = ap.parse_args()
    cfg = json.loads((ROOT / f"artifacts/M7/configs/{a.p1}.json").read_text(encoding="utf-8"))
    out = ROOT / "artifacts/M7/dev/P2"
    if (out / "P2_RESULTS.json").exists():
        sys.exit("refusing to overwrite P2_RESULTS.json")
    p1 = {r["id"]: r for r in json.loads((ROOT / f"artifacts/M7/dev/{a.p1}/BASELINE_RESULTS.json").read_text(encoding="utf-8"))["results"]}
    entries = [e for e in rb.load_entries("dev") if e["dataset"] == "D6" and e["category"] == "syn_words"
               and e["ground_truth"]]
    cache = {}
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        cache[r["key"]] = r
    import torch
    sys.path.insert(0, str(si.UPSTREAM))
    vocab = si.install_vocab(rb.DICT).vocab
    model = None
    rows = []
    with open(CACHE, "a", encoding="utf-8") as cf:
        for e in sorted(entries, key=lambda s: s["id"]):
            assert not si.readable(ROOT / e["file"], e["sha256"])
            rgb = cv2.cvtColor(cv2.imread(str(ROOT / e["file"])), cv2.COLOR_BGR2RGB)
            boxes = m6.segment_words(rgb)
            words, lat = [], 0.0
            for x0, y0, x1, y1 in boxes:
                img, meta = athn.apply(rgb[y0:y1, x0:x1].copy(), cfg)
                k = rb.cache_key("pixels:" + hashlib.sha256(img.tobytes() + str(img.shape).encode()).hexdigest())
                rec = cache.get(k)
                if rec is None:
                    if model is None:
                        model = si.load_model({})
                    with torch.inference_mode():
                        t0 = time.perf_counter()
                        x, m = si.preprocess_array(img)
                        hyp = model.approximate_joint_search(x, m)[0]
                        rec = {"key": k, "image_sha256": e["sha256"], "error": None, "latency_seconds": round(time.perf_counter() - t0, 4),
                               "prediction": "".join(vocab.indices2words(hyp.seq)), "raw_token_ids": hyp.seq, "score": float(hyp.score),
                               "input_shape": list(x.shape), "config_id": "P2-word"}
                    cf.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    cache[k] = rec
                words.append(rec["prediction"])
                lat += rec["latency_seconds"] or 0.0
            pred = " ".join(w for w in words if w)
            rows.append({"id": e["id"], "gt": e["ground_truth"], "gt_value": e["gt_value"], "boxes": len(boxes), "pred_p2": pred,
                         "pred_p1": p1[e["id"]]["prediction"], "value_p2": em.words_value(pred),
                         "value_p1": em.words_value(p1[e["id"]]["prediction"]), "latency_p2_s": round(lat, 4)})
    def score(key):
        tm = em.text_metrics([{"id": r["id"], "gt": r["gt"], "pred": r[f"pred_{key}"]} for r in rows])["primary_failure_aware"]
        val = [r for r in rows if r["gt_value"] is not None]
        return {"cer": tm["cer"], "exact": tm["exact"], "n": tm["n"],
                "value_correct": sum(1 for r in val if r[f"value_{key}"] is not None and r[f"value_{key}"] == Decimal(r["gt_value"])),
                "value_parseable": sum(1 for r in val if r[f"value_{key}"] is not None), "value_n": len(val)}
    s1, s2 = score("p1"), score("p2")
    adopt = s2["value_correct"] - s1["value_correct"] >= 3 and s2["cer"] < s1["cer"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "P2_RESULTS.json").write_text(json.dumps({"p1": a.p1, "p1_full_line": s1, "p2_segmented": s2, "adopt_p2": adopt,
                                                     "rule": ">= 3 more correct written values AND lower CER than P1", "rows": rows},
                                                    indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"p1": s1, "p2": s2, "adopt": adopt}))


if __name__ == "__main__":
    main()
