"""M4-FINAL integrity audit (read-only on data; writes one JSON report).

Checks beyond label differences:
  - duplicate candidates: pixel evidence (ink-mask IoU after resize, mean abs grey difference) + source lineage
  - source cheque identity: distinct source images, repeated amount values / texts across splits
  - blank fields per split; GNHK D1/D5 overlap; global unique image hashes; CVL id field semantics
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\audit_integrity.py OUT.json
"""
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = {"D1_gnhk_subset": "data/public/gnhk/subset/manifest.json", "D4_cvl_numeric": "data/benchmarks/cvl_numeric/manifest.json",
             "D5_gnhk_pairs": "data/benchmarks/gnhk_pairs/manifest.json", "D6_syn_cheques": "data/benchmarks/syn_cheques/manifest.json"}
IOU_DUP, MAD_DUP = 0.85, 8.0   # a "true duplicate" needs near-identical ink AND grey levels


def norm(path, size=(256, 64)):
    a = np.asarray(Image.open(ROOT / path).convert("L").resize(size, Image.BILINEAR), np.float32)
    return a, a < 160


def pair_evidence(a, b):
    ga, ma = norm(a["file"])
    gb, mb = norm(b["file"])
    union = (ma | mb).sum()
    return {"ink_iou": round(float((ma & mb).sum() / union), 3) if union else 1.0,
            "mean_abs_grey_diff": round(float(np.abs(ga - gb).mean()), 2),
            "same_source": a.get("source_sha256") is not None and a.get("source_sha256") == b.get("source_sha256"),
            "same_group": a.get("group_id") == b.get("group_id")}


def main():
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite")
    data = {k: json.loads((ROOT / v).read_text(encoding="utf-8")) for k, v in MANIFESTS.items()}
    samples = {s["id"]: {**s, "_set": k} for k, m in data.items() for s in m["samples"]}
    rep = {"manifests": {k: {"path": v, "entries": len(data[k]["samples"])} for k, v in MANIFESTS.items()}}

    # global entries vs unique images
    by_hash = defaultdict(list)
    for s in samples.values():
        by_hash[s["sha256"]].append(s["id"])
    rep["global"] = {"entries": len(samples), "unique_image_hashes": len(by_hash),
                     "hashes_shared_by_multiple_entries": sum(1 for v in by_hash.values() if len(v) > 1),
                     "shared_hash_cross_split": [v for v in by_hash.values() if len({samples[i]["split"] for i in v}) > 1]}
    for k in MANIFESTS:
        ss = data[k]["samples"]
        rep["manifests"][k].update({"unique_hashes": len({s["sha256"] for s in ss}),
                                    "split": dict(Counter(s["split"] for s in ss)),
                                    "genuine": all(s.get("genuine_handwriting", True) for s in ss)})

    # duplicate candidates reviewed earlier by rule
    review = json.loads((ROOT / "data/benchmarks/duplicate_review.json").read_text(encoding="utf-8"))
    ev, true_dups = [], []
    for r in review:
        a, b = samples[r["pair"][0]], samples[r["pair"][1]]
        e = {"pair": r["pair"], "prior_decision": r["decision"], "gt": [a["ground_truth"], b["ground_truth"]], **pair_evidence(a, b)}
        e["verdict"] = ("true_duplicate" if e["same_source"] or (e["ink_iou"] >= IOU_DUP and e["mean_abs_grey_diff"] <= MAD_DUP
                                                                and a["ground_truth"] == b["ground_truth"] != "")
                        else "blank_template_region" if a["ground_truth"] == b["ground_truth"] == "" else "distinct")
        if e["verdict"] == "true_duplicate":
            true_dups.append(r["pair"])
        ev.append(e)
    rep["duplicate_candidates"] = {"total": len(ev), "verdicts": dict(Counter(e["verdict"] for e in ev)),
                                   "true_duplicates": true_dups,
                                   "distinct_ink_iou_max": max((e["ink_iou"] for e in ev if e["verdict"] == "distinct"), default=None),
                                   "distinct_ink_iou_p95": float(np.percentile([e["ink_iou"] for e in ev if e["verdict"] == "distinct"], 95)),
                                   "rule": f"true duplicate = same source image, or ink IoU >= {IOU_DUP} and mean abs grey diff <= {MAD_DUP} with the same non-blank text",
                                   "evidence": ev}

    # synthetic cheques: source identity and repeated amounts across splits
    syn = data["D6_syn_cheques"]["samples"]
    src = defaultdict(set)
    for s in syn:
        src[s["source_sha256"]].add(s["split"])
    by_text = defaultdict(list)
    for s in syn:
        if s["ground_truth"]:
            by_text[(s["category"], s["ground_truth"])].append(s)
    repeats = []
    for (cat, text), ss in by_text.items():
        if len(ss) > 1:
            for i in range(len(ss)):
                for j in range(i + 1, len(ss)):
                    a, b = ss[i], ss[j]
                    repeats.append({"field": cat, "text": text, "pair": [a["id"], b["id"]], "splits": [a["split"], b["split"]],
                                    "templates": [a["template"], b["template"]], **pair_evidence(a, b)})
    rep["synthetic"] = {"source_images": len(src), "source_images_in_multiple_splits": sum(1 for v in src.values() if len(v) > 1),
                        "templates_by_split": {sp: dict(Counter(s["template"] for s in syn if s["split"] == sp and s["category"] == "syn_num"))
                                               for sp in ("dev", "test")},
                        "repeated_text_pairs": repeats,
                        "repeated_text_cross_split_true_duplicates": [r for r in repeats if r["splits"][0] != r["splits"][1]
                                                                      and r["ink_iou"] >= IOU_DUP and r["mean_abs_grey_diff"] <= MAD_DUP],
                        "blank_fields": {sp: dict(Counter(s["category"] for s in syn if s["split"] == sp and not s["ground_truth"]))
                                         for sp in ("dev", "test")},
                        "license_note": "Apache-2.0 declared on the HF dataset card only; underlying cheque templates (real bank layouts) have undocumented provenance; crops contain only amount fields"}

    # GNHK D1 / D5 overlap
    d1, d5 = data["D1_gnhk_subset"]["samples"], data["D5_gnhk_pairs"]["samples"]
    h1, h5 = {s["sha256"] for s in d1}, {s["sha256"] for s in d5}
    p1, p5 = {s["group_id"] for s in d1}, {s["group_id"] for s in d5}
    split_of_page = {}
    clash = []
    for s in d1 + d5:
        if split_of_page.setdefault(s["group_id"], s["split"]) != s["split"]:
            clash.append(s["id"])
    rep["gnhk_overlap"] = {"entries": len(d1) + len(d5), "unique_hashes": len(h1 | h5), "shared_crops": len(h1 & h5),
                           "unique_pages": len(p1 | p5), "shared_pages": len(p1 & p5), "page_split_conflicts": clash}

    # CVL id semantics
    z = zipfile.ZipFile(ROOT / "data/public/cvl/cache/cvl-strings-train.zip")
    readme = z.read("readme").decode("latin-1")
    rep["cvl"] = {"readme_excerpt": readme.split("File Naming:")[1].strip()[:300],
                  "writer_field_documented": "writer" in readme.split("File Naming:")[1].lower(),
                  "unique_hashes_in_subset": len({s["sha256"] for s in data["D4_cvl_numeric"]["samples"]}),
                  "status": "second filename field is described only as a 'unique ID'; used as an INFERRED writer/session id"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("duplicate_candidates", "synthetic")}, indent=1)[:2500])
    dc = rep["duplicate_candidates"]
    print("dups:", dc["verdicts"], "true:", dc["true_duplicates"], "distinct IoU max/p95:", dc["distinct_ink_iou_max"], dc["distinct_ink_iou_p95"])
    sy = rep["synthetic"]
    print("syn:", {k: sy[k] for k in ("source_images", "source_images_in_multiple_splits", "templates_by_split", "blank_fields")},
          "repeated text pairs:", [(r["text"], r["splits"], r["ink_iou"], r["mean_abs_grey_diff"]) for r in sy["repeated_text_pairs"]],
          "cross-split true dups:", len(sy["repeated_text_cross_split_true_duplicates"]))


if __name__ == "__main__":
    main()
