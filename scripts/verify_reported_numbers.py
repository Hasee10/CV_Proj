"""Check every headline number quoted in the handover documents against the saved M8 evidence (read-only).
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\verify_reported_numbers.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
cm = json.loads((ROOT / "artifacts/M8/COMPARATIVE_METRICS.json").read_text(encoding="utf-8"))
st = json.loads((ROOT / "artifacts/M8/STATISTICAL_ANALYSIS.json").read_text(encoding="utf-8"))["results"]
d, p = cm["datasets"], cm["pairs"]
r3 = lambda x: round(x, 3)
CLAIMS = [
    ("synthetic numeric CER 1.014 -> 0.599", (r3(d["D6_syn_numeric_SYNTHETIC"]["cer"]["baseline"]), r3(d["D6_syn_numeric_SYNTHETIC"]["cer"]["proposed"])), (1.014, 0.599)),
    ("synthetic numeric correct values 0/77 -> 17/77", (d["D6_syn_numeric_SYNTHETIC"]["value_exact"]["baseline"], d["D6_syn_numeric_SYNTHETIC"]["value_exact"]["proposed"], d["D6_syn_numeric_SYNTHETIC"]["value_exact"]["n"]), (0, 17, 77)),
    ("GNHK CER 0.296 -> 0.252", (r3(d["D1_gnhk_words_genuine"]["cer"]["baseline"]), r3(d["D1_gnhk_words_genuine"]["cer"]["proposed"])), (0.296, 0.252)),
    ("GNHK exact 73/160 -> 78/160", (d["D1_gnhk_words_genuine"]["exact"]["baseline"], d["D1_gnhk_words_genuine"]["exact"]["proposed"], d["D1_gnhk_words_genuine"]["n_eligible"]), (73, 78, 160)),
    ("CVL exact 97/210 both", (d["D4_cvl_numeric_genuine"]["exact"]["baseline"], d["D4_cvl_numeric_genuine"]["exact"]["proposed"], d["D4_cvl_numeric_genuine"]["n_eligible"]), (97, 97, 210)),
    ("CVL CER 0.141 -> 0.143", (r3(d["D4_cvl_numeric_genuine"]["cer"]["baseline"]), r3(d["D4_cvl_numeric_genuine"]["cer"]["proposed"])), (0.141, 0.143)),
    ("genuine aggregate CER change -0.015", r3(st["ALL_GENUINE"]["cer_delta"]), -0.015),
    ("genuine aggregate 95% CI [-0.036, 0.002]", [r3(v) for v in st["ALL_GENUINE"]["cer_delta_ci95"]], [-0.036, 0.002]),
    ("synthetic numeric CER change CI [-0.534, -0.296]", [r3(v) for v in st["D6_syn_numeric_SYNTHETIC"]["cer_delta_ci95"]], [-0.534, -0.296]),
    ("GNHK constructed pairs decided 24/52 -> 27/52",
     tuple(52 - p["gnhk_pairs_genuine_constructed"][m]["decisions"].get("review", 0) for m in ("baseline", "proposed")) + (p["gnhk_pairs_genuine_constructed"]["baseline"]["n_eligible"],), (24, 27, 52)),
    ("GNHK pairs: no mismatch accepted", (p["gnhk_pairs_genuine_constructed"]["baseline"]["incorrect_acceptance_rate"], p["gnhk_pairs_genuine_constructed"]["proposed"]["incorrect_acceptance_rate"]), (0.0, 0.0)),
    ("synthetic verification all-review (both)", (p["syn_all_SYNTHETIC"]["baseline"]["all_review"], p["syn_all_SYNTHETIC"]["proposed"]["all_review"]), (True, True)),
    ("synthetic written value accuracy zero (both)", (d["D6_syn_words_SYNTHETIC"]["value_exact"]["baseline"], d["D6_syn_words_SYNTHETIC"]["value_exact"]["proposed"]), (0, 0)),
    ("genuine exact improved 19 / regressed 10", (st["ALL_GENUINE"]["exact_mcnemar"]["improved"], st["ALL_GENUINE"]["exact_mcnemar"]["regressed"]), (19, 10)),
]


def main():
    out = [{"claim": c, "evidence": a, "expected": e, "ok": a == e} for c, a, e in CLAIMS]
    for x in out:
        print(("ok " if x["ok"] else "BAD"), x["claim"], x["evidence"])
    print(f"{sum(x['ok'] for x in out)}/{len(out)} claims match the saved evidence")
    if "--json" in sys.argv:
        print(json.dumps(out))
    return 0 if all(x["ok"] for x in out) else 1


if __name__ == "__main__":
    sys.exit(main())
