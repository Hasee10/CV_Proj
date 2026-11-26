"""Apply the frozen M7 selection protocol (artifacts/M7/SELECTION_PROTOCOL.md) to scored dev runs.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m7_select.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A7 = ROOT / "artifacts/M7"
CANDIDATES, ABLATIONS = ["P1-A", "P1-B", "P1-C"], ["B1", "P1-D"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def summary(d: Path):
    m = json.loads((d / "METRICS.json").read_text(encoding="utf-8"))["groups"]
    pr = json.loads((d / "PAIR_RESULTS.json").read_text(encoding="utf-8"))
    rt = json.loads((d / "RUNTIME_REPORT.json").read_text(encoding="utf-8"))
    res = json.loads((d / "BASELINE_RESULTS.json").read_text(encoding="utf-8"))["results"]
    g = lambda k: m[k]["primary_failure_aware"]
    syn = pr["metrics"]["syn_all_SYNTHETIC"]
    pairs = [p for p in pr["pairs"] if p["dataset"] == "syn_cheques"]
    pre = sorted(r["preprocess"].get("preprocess_seconds", 0) for r in res if r.get("preprocess"))
    return {
        "D1": {"exact": g("D1_gnhk_words_genuine")["exact"], "cer": round(g("D1_gnhk_words_genuine")["cer"], 4)},
        "D4": {"exact": g("D4_cvl_numeric_genuine")["exact"], "cer": round(g("D4_cvl_numeric_genuine")["cer"], 4),
               "value_exact": m["D4_cvl_numeric_genuine"]["amount_value"]["exact"]},
        "D5": {"exact_num": g("D5_gnhk_numeric_genuine")["exact"], "exact_words": g("D5_gnhk_words_genuine")["exact"]},
        "D6_num": {"exact": g("D6_syn_numeric_SYNTHETIC")["exact"], "cer": round(g("D6_syn_numeric_SYNTHETIC")["cer"], 4),
                   "value_exact": m["D6_syn_numeric_SYNTHETIC"]["amount_value"]["exact"],
                   "parseable": m["D6_syn_numeric_SYNTHETIC"]["amount_value"]["parseable"]},
        "D6_words": {"exact": g("D6_syn_words_SYNTHETIC")["exact"], "cer": round(g("D6_syn_words_SYNTHETIC")["cer"], 4),
                     "value_exact": m["D6_syn_words_SYNTHETIC"]["amount_value"]["exact"],
                     "parseable": m["D6_syn_words_SYNTHETIC"]["amount_value"]["parseable"]},
        "D6_pairs": {"decisions": syn["decisions"], "correct_auto": sum(1 for p in pairs if (p["label"], p["decision"]) in (("match", "accept"), ("mismatch", "flag"))),
                     "incorrect_acceptance_rate": syn["incorrect_acceptance_rate"], "review_rate": syn["manual_review_rate"],
                     "all_review": syn["all_review"]},
        "latency_median_s": rt["latency_all_unique_inputs"]["median"], "latency_p95_s": rt["latency_all_unique_inputs"]["p95"],
        "preprocess_median_s": pre[len(pre) // 2] if pre else 0.0,
        "resized": sum(1 for r in res if r.get("preprocess", {}).get("applied")),
        "resized_genuine": sum(1 for r in res if r.get("preprocess", {}).get("applied") and r["dataset"] in ("D1", "D4", "D5")),
    }


def guardrails(s, b0):
    checks = {"D1_cer": s["D1"]["cer"] - b0["D1"]["cer"] <= 0.02, "D1_exact": b0["D1"]["exact"] - s["D1"]["exact"] <= 2,
              "D4_cer": s["D4"]["cer"] - b0["D4"]["cer"] <= 0.02, "D4_exact": b0["D4"]["exact"] - s["D4"]["exact"] <= 2,
              "D4_value": b0["D4"]["value_exact"] - s["D4"]["value_exact"] <= 2,
              "incorrect_acceptance": (s["D6_pairs"]["incorrect_acceptance_rate"] or 0) <= 0.10,
              "latency": s["latency_median_s"] <= 0.90,
              "not_all_review_unless_baseline": (not s["D6_pairs"]["all_review"]) or b0["D6_pairs"]["all_review"]}
    return checks, all(checks.values())


def main():
    for cid in CANDIDATES + ABLATIONS:
        d = A7 / "dev" / cid
        if not (d / "METRICS.json").exists():
            subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "scripts/score_baseline.py"), "--dir", str(d)], check=True,
                           capture_output=True)
    b0 = summary(ROOT / "artifacts/M5_DEV")
    rows = {"B0": b0}
    for cid in CANDIDATES + ABLATIONS:
        rows[cid] = summary(A7 / "dev" / cid)
        rows[cid]["guardrails"], rows[cid]["passes"] = guardrails(rows[cid], b0)
    passing = [c for c in CANDIDATES if rows[c]["passes"]]
    order = sorted(passing, key=lambda c: (-rows[c]["D6_num"]["value_exact"], -rows[c]["D6_pairs"]["correct_auto"],
                                           rows[c]["D1"]["cer"] + rows[c]["D4"]["cer"], rows[c]["resized_genuine"], c))
    chosen = order[0] if order else None
    success = bool(chosen) and rows[chosen]["D6_num"]["value_exact"] - b0["D6_num"]["value_exact"] >= 3
    (A7 / "DEVELOPMENT_RESULTS.json").write_text(json.dumps({"protocol": "artifacts/M7/SELECTION_PROTOCOL.md", "split": "dev",
                                                             "results": rows, "passing_candidates": passing, "ranking": order,
                                                             "selected": chosen, "success_rule_met": success}, indent=1), encoding="utf-8")
    print(json.dumps({k: {kk: v[kk] for kk in ("D1", "D4", "D6_num", "D6_words", "D6_pairs", "latency_median_s", "resized_genuine")}
                      | ({"passes": v["passes"], "failed": [g for g, ok in v["guardrails"].items() if not ok]} if "passes" in v else {})
                      for k, v in rows.items()}, indent=1))
    print("passing", passing, "ranking", order, "selected", chosen, "success", success)


if __name__ == "__main__":
    main()
