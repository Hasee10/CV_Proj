"""M3-B correction pass: apply audited ground truth to the ORIGINAL M3-B predictions.

Reads artifacts/M3_B/ (never writes there) and writes artifacts/M3_B_corrected/.
Predictions and token ids are copied unchanged (asserted). Only ground truth, ambiguity notes
and derived metrics change. Every alternative reading is scored as a sensitivity check.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m3b_correct.py
"""
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import m3b_metrics  # noqa: E402
from smoke_inference import edit_distance  # noqa: E402

SRC = ROOT / "artifacts" / "M3_B"
DST = ROOT / "artifacts" / (sys.argv[1] if len(sys.argv) > 1 else "M3_B_corrected")  # M3_B_final = final version
# label provenance: everything not listed here is a visual reading confirmed by the supervisor audit
LABEL_STATUS = {"H04": "ambiguous_visual_reading", "H05": "writer_confirmed"}
PRED = "SSL_HWD_Dict.txt"

# sample id -> corrected primary ground truth, alternatives, strict-punctuation eligibility, note
CORRECTIONS = {
    "H04": {"ground_truth": "1250-00", "alternatives": ["1250.00"], "punctuation_strict_eligible": False,
            "note": "Separator between '1250' and '00' is a short, slightly sloped stroke at mid-low height; it looks "
                    "closer to '-' than to '.', but is ambiguous. Primary GT is the visual reading '1250-00'; the writer's "
                    "intended '1250.00' is scored as an alternative. Excluded from strict punctuation evaluation."},
    "H05": {"ground_truth": "75,450.50", "alternatives": [], "punctuation_strict_eligible": True,
            "note": "Visual audit proposed '75,430.50'. Resolved as '75,450.50': the writer confirmed it on 2026-11-26, "
                    "and side-by-side comparison shows the digit matches the writer's other two '5' glyphs. "
                    "Comma and decimal point are clear and remain in strict punctuation evaluation."},
}


def base_id(sid: str) -> str:
    return sid.split("-")[0]


def score(pred: str, gt: str) -> dict:
    ed = edit_distance(pred, gt)
    return {"ground_truth": gt, "exact": pred == gt, "char_edit_distance": ed, "cer": round(ed / len(gt), 4)}


def main():
    orig = json.loads((SRC / "INFERENCE_RESULTS.json").read_text(encoding="utf-8"))
    man = json.loads((SRC / "DATA_MANIFEST.json").read_text(encoding="utf-8"))
    assert DST != SRC and not (DST / "INFERENCE_RESULTS.json").exists() or DST.name == "M3_B_corrected", "refusing to overwrite"
    DST.mkdir(exist_ok=True)
    rep = json.loads(json.dumps(orig))  # deep copy
    for r in rep["results"]:
        r["label_status"] = LABEL_STATUS.get(base_id(r["id"]), "visual_reading_confirmed_by_audit")
        c = CORRECTIONS.get(base_id(r["id"]))
        if not c:
            continue
        pred = r["prediction_by_dict"][PRED]
        r["ground_truth_original_m3b"] = r["ground_truth"]
        r["ground_truth"] = c["ground_truth"]
        r["exact_match_by_dict"] = {k: v == c["ground_truth"] for k, v in r["prediction_by_dict"].items()}
        r["char_edit_distance"] = edit_distance(pred, c["ground_truth"])
        r["cer"] = round(r["char_edit_distance"] / len(c["ground_truth"]), 4)
        r["punctuation_strict_eligible"] = c["punctuation_strict_eligible"]
        r["ambiguity_note"] = c["note"]
        r["alternative_readings"] = [score(pred, g) for g in c["alternatives"]]
    for a, b in zip(orig["results"], rep["results"]):  # predictions must be untouched
        assert a["id"] == b["id"] and a["raw_token_ids"] == b["raw_token_ids"]
        assert a["prediction_by_dict"] == b["prediction_by_dict"] and a.get("latency_seconds") == b.get("latency_seconds")
    rep["correction_pass"] = "Ground truth corrected after visual audit; predictions are the original M3-B outputs."
    (DST / "INFERENCE_RESULTS.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")

    for s in man["samples"]:
        s["label_status"] = LABEL_STATUS.get(base_id(s["id"]), "visual_reading_confirmed_by_audit")
        c = CORRECTIONS.get(base_id(s["id"]))
        if c:
            s.update({"ground_truth_original_m3b": s["ground_truth"], "ground_truth": c["ground_truth"],
                      "ground_truth_alternatives": c["alternatives"],
                      "punctuation_strict_eligible": c["punctuation_strict_eligible"], "notes": c["note"]})
    man["correction_pass"] = {"date": "2026-11-26", "reason": "supervisor visual audit",
                              "changed_ids": sorted(CORRECTIONS), "original_manifest_sha256": man.get("frozen_manifest_sha256"),
                              "note": "Original frozen manifest and M3-B artifacts are unchanged; this file supersedes them for ground truth only."}
    (DST / "DATA_MANIFEST.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")

    m3b_metrics.main(DST.name)
    metrics = json.loads((DST / "METRICS.json").read_text(encoding="utf-8"))
    # sensitivity: aggregate CER / exact for every combination of readings, per condition
    combos = list(itertools.product(*[[c["ground_truth"]] + c["alternatives"] for c in CORRECTIONS.values()]))
    sens = []
    for combo in combos:
        gts = dict(zip(CORRECTIONS, combo))
        row = {"readings": gts}
        for cond in ("crop", "full_photo"):
            rows = [r for r in rep["results"] if r["condition"] == cond]
            ed = n = ex = 0
            for r in rows:
                gt = gts.get(base_id(r["id"]), r["ground_truth"])
                p = r["prediction_by_dict"][PRED]
                ed += edit_distance(p, gt)
                n += len(gt)
                ex += p == gt
            row[cond] = {"exact": f"{ex}/{len(rows)}", "char_edit_distance": ed, "gt_chars": n, "aggregate_cer": round(ed / n, 4)}
        sens.append(row)
    metrics["sensitivity_ground_truth_readings"] = sens
    (DST / "METRICS.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sens, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
