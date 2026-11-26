"""M3-B aggregates from artifacts/M3_B/INFERENCE_RESULTS.json (raw predictions, SSL_HWD_Dict.txt).

Aggregate CER = total character edit distance / total ground-truth characters.
The digits-only and case-insensitive views are labelled secondary comparisons, never the primary result.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m3b_metrics.py
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from smoke_inference import edit_distance  # noqa: E402

PUNCT_IDS = {",": 15, ".": 17}


def agg(rows):
    ok = [r for r in rows if not r["error"]]
    ed = sum(r["char_edit_distance"] for r in ok)
    n = sum(len(r["ground_truth"]) for r in ok)
    lat = [r["latency_seconds"] for r in ok]
    return {"samples": len(rows), "errors": len(rows) - len(ok),
            "exact_match": f"{sum(r['exact_match_by_dict']['SSL_HWD_Dict.txt'] for r in ok)}/{len(rows)}",
            "char_edit_distance": ed, "gt_chars": n, "aggregate_cer": round(ed / n, 4) if n else None,
            "median_latency_s": round(statistics.median(lat), 4) if lat else None}


def main(art: str = "M3_B"):  # art: artifact folder name, e.g. M3_B_corrected
    res = json.loads((ROOT / "artifacts" / art / "INFERENCE_RESULTS.json").read_text(encoding="utf-8"))["results"]
    out = {}
    for cond in ("crop", "full_photo", "segmented_word"):
        rows = [r for r in res if r["condition"] == cond]
        out[cond] = {"all": agg(rows)}
        for cat in sorted({r["category"] for r in rows}):
            out[cond][cat] = agg([r for r in rows if r["category"] == cat])
        num = [r for r in rows if r["category"].startswith("numeric")]
        out[cond]["numeric_all"] = agg(num) if num else None
        out[cond]["punctuation"] = [
            {"id": r["id"], "gt_symbol": s, "gt_count": r["ground_truth"].count(s),
             "emitted_count": r["raw_token_ids"].count(i)}
            for r in rows for s, i in PUNCT_IDS.items()
            if s in r["ground_truth"] and r.get("punctuation_strict_eligible", True)]
        out[cond]["punctuation_excluded_ambiguous"] = [r["id"] for r in rows if r.get("punctuation_strict_eligible") is False]
        # SECONDARY, labelled: digits-only for numeric samples; case-insensitive for words
        out[cond]["secondary_digits_only_numeric_exact"] = (
            f"{sum(''.join(c for c in r['prediction_by_dict']['SSL_HWD_Dict.txt'] if c.isdigit()) == ''.join(c for c in r['ground_truth'] if c.isdigit()) for r in num)}/{len(num)}"
            if num else None)
        wl = [r for r in rows if not r["category"].startswith("numeric")]
        out[cond]["secondary_case_insensitive_word_exact"] = (
            f"{sum(r['prediction_by_dict']['SSL_HWD_Dict.txt'].lower() == r['ground_truth'].lower() for r in wl)}/{len(wl)}"
            if wl else None)
        out[cond]["space_token_emitted_any"] = any(r.get("space_token_emitted") for r in rows)
    h09 = next(r for r in res if r["id"] == "H09")
    joined = "".join(r["ground_truth"] for r in res if r["condition"] == "segmented_word")
    out["multiword_H09_vs_unspaced_gt_secondary"] = {
        "gt_without_spaces": joined, "prediction": h09["prediction_by_dict"]["SSL_HWD_Dict.txt"],
        "char_edit_distance": edit_distance(h09["prediction_by_dict"]["SSL_HWD_Dict.txt"], joined)}
    path = ROOT / "artifacts" / art / "METRICS.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:2])
