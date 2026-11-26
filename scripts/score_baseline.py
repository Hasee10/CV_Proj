"""Score saved baseline predictions with the frozen metrics (no inference). Reproducible from BASELINE_RESULTS.json.

Outputs (refuses to overwrite): METRICS.json, PAIR_RESULTS.json, RUNTIME_REPORT.json in --dir.
Recognition: eligible = non-empty ground truth; blank fields reported separately. Genuine and synthetic never pooled.
Values: numeric_value() for numeric fields, words_value() for word fields; reference values come from the manifests.
Pairs: decide(numeric_value(pred_num), words_value(pred_words)) vs the manifest pair label.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\score_baseline.py --dir artifacts\\M5_DEV
"""
import argparse
import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eval_metrics as em  # noqa: E402

NUMERIC_CATS = {"cvl_numeric", "gnhk_numeric", "syn_num"}
WORD_CATS = {"gnhk_word", "syn_words"}


def failed(r):
    return bool(r["error"]) or r["prediction"] is None


def pred_of(r):
    return "" if failed(r) else r["prediction"]


def value_of(r):
    p = None if failed(r) else r["prediction"]
    return em.numeric_value(p) if r["category"] in NUMERIC_CATS else em.words_value(p)


def group_metrics(rows):
    elig = [r for r in rows if r["recognition_eligible"]]
    tm = em.text_metrics([{"id": r["id"], "gt": r["ground_truth"], "pred": r["prediction"], "error": r["error"]} for r in elig])
    out = {"entries": len(rows), "unique_inputs": len({r["input_sha256"] for r in rows}), "eligible": len(elig),
           "blank_fields": len(rows) - len(elig), **tm,
           "latency": em.latency_stats([r["latency_seconds"] for r in rows if r["latency_seconds"] is not None])}
    val = [r for r in elig if r.get("gt_value") is not None]
    if val:
        vals = [value_of(r) for r in val]
        out["amount_value"] = {"n": len(val), "parseable": sum(v is not None for v in vals),
                               "exact": sum(v is not None and v == Decimal(r["gt_value"]) for v, r in zip(vals, val)),
                               "kind": sorted({"numeric" if r["category"] in NUMERIC_CATS else "written" for r in val})}
        out["amount_value"]["exact_rate"] = out["amount_value"]["exact"] / len(val)
    return out


def classify(r):
    """Descriptive error categories for one eligible, wrong prediction (multi-label)."""
    gt, pr = r["ground_truth"], pred_of(r)
    cats = set()
    if failed(r):
        return {"inference_failure"}
    if pr == "":
        cats.add("empty_prediction")
    ops, _ = em.align(pr, gt)
    for k, (op, p, g) in enumerate(ops):
        if op == "extra" and p == "0" and ("0" in gt):
            cats.add("repeated_zero_insertion")
        elif op == "missing" and g == "0" and gt.count("0") >= 2:
            cats.add("repeated_zero_deletion")
        elif op == "sub" and p and g and p.isdigit() and g.isdigit():
            cats.add("digit_substitution")
        elif op != "match" and g == ".":
            cats.add("missing_or_wrong_decimal_point")
        elif op != "match" and g == ",":
            cats.add("missing_or_wrong_thousands_separator")
        elif op != "match" and g == " ":
            cats.add("missing_space")
        elif op == "missing" and g and g.isalpha():
            cats.add("letter_omission")
        elif op == "extra" and p and p.isalpha():
            cats.add("letter_insertion")
        elif op == "sub" and p and g and p.isalpha() and g.isalpha():
            cats.add("letter_substitution" if p.lower() != g.lower() else "case_error")
        elif op != "match" and g and g in "/-:()":
            cats.add("other_punctuation_error")
    if " " in gt and " " not in pr and pr:
        cats.add("multiword_collapsed")
    if r.get("gt_value") is not None and value_of(r) is None:
        cats.add("invalid_financial_parse")
    return cats or {"other"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--split", default="dev")
    a = ap.parse_args()
    d = Path(a.dir)
    for f in ("METRICS.json", "PAIR_RESULTS.json", "RUNTIME_REPORT.json"):
        if (d / f).exists():
            raise SystemExit(f"{d / f} exists; refusing to overwrite")
    base = json.loads((d / "BASELINE_RESULTS.json").read_text(encoding="utf-8"))
    rows, run = base["results"], base["run"]
    assert all(r["split"] == a.split for r in rows), f"sample outside the {a.split} split in results"
    by_id = {r["id"]: r for r in rows}
    groups = {
        "D1_gnhk_words_genuine": [r for r in rows if r["dataset"] == "D1"],
        "D1_digit_stratum": [r for r in rows if r["dataset"] == "D1" and r["stratum"] == "digit"],
        "D1_other_stratum": [r for r in rows if r["dataset"] == "D1" and r["stratum"] == "other"],
        "D4_cvl_numeric_genuine": [r for r in rows if r["dataset"] == "D4"],
        "D5_gnhk_numeric_genuine": [r for r in rows if r["category"] == "gnhk_numeric"],
        "D5_gnhk_words_genuine": [r for r in rows if r["category"] == "gnhk_word"],
        "D6_syn_numeric_SYNTHETIC": [r for r in rows if r["category"] == "syn_num"],
        "D6_syn_words_SYNTHETIC": [r for r in rows if r["category"] == "syn_words"],
    }
    for t in sorted({r["template"] for r in rows if r["template"]}):
        for c, lab in (("syn_num", "numeric"), ("syn_words", "words")):
            groups[f"D6_{lab}_{t.split()[0]}_SYNTHETIC"] = [r for r in rows if r["template"] == t and r["category"] == c]
    metrics = {"scope": f"{a.split.upper()} split only; genuine and synthetic reported separately; no pooled overall score",
               "groups": {k: group_metrics(v) for k, v in groups.items()}}

    # pairs
    pairs = [p for p in json.loads((ROOT / "data/benchmarks/amount_pairs.json").read_text(encoding="utf-8"))["pairs"]
             if p["split"] == a.split]
    presults = []
    for p in pairs:
        n, w = by_id[p["num_id"]], by_id[p["words_id"]]
        nv, wv = value_of(n), value_of(w)
        presults.append({"pair_id": p["pair_id"], "dataset": p["dataset"], "construction": p["construction"],
                         "label": p["label"], "num_id": n["id"], "words_id": w["id"], "num_prediction": n["prediction"],
                         "words_prediction": w["prediction"], "num_value_pred": None if nv is None else str(nv),
                         "words_value_pred": None if wv is None else str(wv), "num_value_ref": p["num_value"],
                         "words_value_ref": p["words_value"], "decision": em.decide(nv, wv)})
    pm = {}
    for name, sel in (("gnhk_pairs_genuine_constructed", lambda x: x["dataset"] == "gnhk_pairs"),
                      ("syn_all_SYNTHETIC", lambda x: x["dataset"] == "syn_cheques"),
                      ("syn_natural_SYNTHETIC", lambda x: x["dataset"] == "syn_cheques" and x["construction"].startswith("natural")),
                      ("syn_constructed_SYNTHETIC", lambda x: x["dataset"] == "syn_cheques" and x["construction"].startswith("constructed"))):
        ps = [x for x in presults if sel(x)]
        m = em.discrepancy_metrics([{"id": x["pair_id"], "label": x["label"], "decision": x["decision"]} for x in ps])
        m["labels"] = dict(Counter(x["label"] for x in ps))
        m["decisions"] = dict(Counter(x["decision"] for x in ps))
        m["unresolved_pair_decisions"] = dict(Counter(x["decision"] for x in ps if x["label"] == "unresolved"))
        elig = [x for x in ps if x["label"] in ("match", "mismatch")]
        m["decided_only_coverage"] = (sum(1 for x in elig if x["decision"] != "review") / len(elig)) if elig else None
        m["automatic_acceptance"] = {"matches": sum(1 for x in elig if x["label"] == "match"),
                                     "matches_accepted": sum(1 for x in elig if x["label"] == "match" and x["decision"] == "accept")}
        pm[name] = m
    # failure inventory
    wrong = [r for r in rows if r["recognition_eligible"] and pred_of(r) != r["ground_truth"]]
    cat_rows = {}
    for r in wrong:
        for c in classify(r):
            cat_rows.setdefault(c, []).append(r)
    lat = sorted(r["latency_seconds"] for r in rows if r["latency_seconds"] is not None)
    p95 = em.latency_stats(lat)["p95"]
    inventory = {"wrong_eligible": len(wrong), "eligible": sum(r["recognition_eligible"] for r in rows),
                 "categories": {c: {"samples": len(v), "by_dataset": dict(Counter(r["dataset"] for r in v)),
                                    "examples": [{"id": r["id"], "dataset": r["dataset"], "gt": r["ground_truth"],
                                                  "pred": r["prediction"]} for r in sorted(v, key=lambda r: r["id"])[:4]]}
                                for c, v in sorted(cat_rows.items(), key=lambda kv: -len(kv[1]))},
                 "pair_outcomes": {"false_acceptance": [x["pair_id"] for x in presults if x["label"] == "mismatch" and x["decision"] == "accept"],
                                   "false_rejection_flag": [x["pair_id"] for x in presults if x["label"] == "match" and x["decision"] == "flag"],
                                   "review": sum(1 for x in presults if x["decision"] == "review")},
                 "slow_inference_over_p95": [{"id": r["id"], "latency": r["latency_seconds"], "shape": r["input_shape"]}
                                             for r in rows if r["latency_seconds"] and r["latency_seconds"] > p95]}
    metrics["failure_inventory"] = inventory
    runtime = {"run": {k: v for k, v in run.items() if k in ("torch", "threads", "python", "model_load_seconds", "warmup_seconds",
                                                            "entries", "unique_inputs", "computed_this_run", "reused_from_cache",
                                                            "wall_seconds", "inference_seconds_computed", "checkpoint_sha256")},
               "pilot": ("BASELINE_RESULTS_pilot5.json (18 entries, 4.98 s inference, median 0.1507 s; reused in full run)" if (d / "BASELINE_RESULTS_pilot5.json").exists() else None),
               "latency_all_unique_inputs": em.latency_stats(lat),
               "latency_by_dataset": {ds: em.latency_stats([r["latency_seconds"] for r in rows if r["dataset"] == ds and r["cache_status"] != "dedup_same_image"])
                                      for ds in ("D1", "D4", "D5", "D6")},
               "height_vs_latency_note": "latency grows with input size and decoded length (see slow list in METRICS)",
               "cpu": "Intel Core i7-1265U, 10 torch threads, batch 1"}
    (d / "METRICS.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (d / "PAIR_RESULTS.json").write_text(json.dumps({"metrics": pm, "pairs": presults}, indent=1, ensure_ascii=False), encoding="utf-8")
    (d / "RUNTIME_REPORT.json").write_text(json.dumps(runtime, indent=1), encoding="utf-8")
    for k, v in metrics["groups"].items():
        p = v["primary_failure_aware"]
        av = v.get("amount_value", {})
        print(f"{k:34} n={v['eligible']:3} exact={p['exact']}/{p['n']} cer={p['cer']:.3f} wer={p['wer']:.3f} "
              f"punct P/R={p['punctuation']['precision']}/{p['punctuation']['recall']} "
              f"value={av.get('exact')}/{av.get('n')} parse={av.get('parseable')} blank={v['blank_fields']} "
              f"lat_med={v['latency']['median']} p95={v['latency']['p95']}")
    for k, m in pm.items():
        print(k, m["labels"], m["decisions"], "IAR", m["incorrect_acceptance_rate"], "IRR", m["incorrect_rejection_rate"],
              "review", m["manual_review_rate"], "prim", {x: m["primary_flag_or_review_positive"][x] for x in ("precision", "recall", "f1")},
              "decided", {x: m["secondary_decided_only"][x] for x in ("precision", "recall", "f1", "n_decided")}, "all_review", m["all_review"],
              "cov", m["decided_only_coverage"], "auto", m["automatic_acceptance"])
    print({c: v["samples"] for c, v in inventory["categories"].items()}, "wrong", inventory["wrong_eligible"], "/", inventory["eligible"])
    print("pair outcomes", {k: (len(v) if isinstance(v, list) else v) for k, v in inventory["pair_outcomes"].items()},
          "slow", len(inventory["slow_inference_over_p95"]))


if __name__ == "__main__":
    main()
