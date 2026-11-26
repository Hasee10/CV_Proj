"""Freeze the M7 selection: FROZEN_CONFIG.json, ABLATION_RESULTS.json, SUMMARY.json (dev evidence only).
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m7_freeze.py
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import smoke_inference as si  # noqa: E402

A7 = ROOT / "artifacts/M7"
SOURCES = ["scripts/athn.py", "scripts/run_method.py", "scripts/smoke_inference.py", "scripts/run_baseline.py",
           "scripts/eval_metrics.py", "scripts/score_baseline.py", "scripts/m7_select.py", "scripts/m7_p2.py",
           "scripts/m6_prepare.py", "artifacts/M7/SELECTION_PROTOCOL.md"]


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def main():
    for f in ("FROZEN_CONFIG.json", "ABLATION_RESULTS.json", "SUMMARY.json"):
        if (A7 / f).exists():
            sys.exit(f"refusing to overwrite {f}")
    dev = json.loads((A7 / "DEVELOPMENT_RESULTS.json").read_text(encoding="utf-8"))
    p2 = json.loads((A7 / "dev/P2/P2_RESULTS.json").read_text(encoding="utf-8"))
    assert (A7 / "PROTOCOL_FROZEN.sha256").read_text().split()[0] == sha("artifacts/M7/SELECTION_PROTOCOL.md")
    chosen = dev["selected"]
    cfg_path = f"artifacts/M7/configs/{chosen}.json"
    frozen_manifests = json.loads((ROOT / "artifacts/M4_FINAL/SUMMARY.json").read_text(encoding="utf-8"))["frozen_manifests_sha256"]
    status = "VERIFIED" if dev["success_rule_met"] else "PARTIAL"
    frozen = {"milestone": "M7", "status": status, "selected": chosen, "method_config": json.loads((ROOT / cfg_path).read_text(encoding="utf-8")),
              "method_config_file": cfg_path, "method_config_sha256": sha(cfg_path),
              "p2_word_segmentation": {"adopted": p2["adopt_p2"], "reason": "frozen rule: >= 3 more correct written values and lower CER"},
              "backend_default_mode": "proposed" if dev["success_rule_met"] else "baseline",
              "backend_default_rule": "declared before M8: proposed if the M7 dev success rule is met, else baseline",
              "dev_results_file": f"artifacts/M7/dev/{chosen}/BASELINE_RESULTS.json",
              "checkpoint_sha256": si.CKPT_SHA256, "upstream_commit": "9eaea5fe", "dictionary": "SSL_HWD_Dict.txt",
              "frozen_manifests_sha256": frozen_manifests, "source_sha256": {p: sha(p) for p in SOURCES},
              "selection_used": "dev split only; the locked test split was never read in M7"}
    r = dev["results"]
    abl = {"split": "dev", "note": "B0 = M5 baseline predictions (reused). B1/P1-D are ablations (not selectable).",
           "rows": {k: {kk: r[k][kk] for kk in ("D1", "D4", "D5", "D6_num", "D6_words", "D6_pairs", "latency_median_s",
                                                "latency_p95_s", "resized", "resized_genuine")} | {"passes_guardrails": r[k].get("passes")}
                    for k in ("B0", "B1", "P1-A", "P1-B", "P1-C", "P1-D")},
           "P2": {"base": chosen, "p1_full_line": p2["p1_full_line"], "p2_segmented": p2["p2_segmented"], "adopted": p2["adopt_p2"]},
           "what_each_ablation_isolates": {"B1": "resizing without adaptivity (every crop 2x)",
                                           "P1-D": "adaptivity without shrinking (enlarge only)",
                                           "P1-B/P1-C": "band width / target sensitivity",
                                           "P2": "word segmentation on top of the selected ATHN"}}
    summ = {"milestone": "M7", "status": status, "method": "Adaptive Text-Height Normalisation (ATHN), training-free",
            "selected": chosen, "success_rule_met": dev["success_rule_met"], "passing_candidates": dev["passing_candidates"],
            "dev_primary_objective_D6_numeric_value_exact": {"B0": r["B0"]["D6_num"]["value_exact"], chosen: r[chosen]["D6_num"]["value_exact"], "n": 35},
            "dev_genuine": {"D1_exact": [r["B0"]["D1"]["exact"], r[chosen]["D1"]["exact"]], "D1_cer": [r["B0"]["D1"]["cer"], r[chosen]["D1"]["cer"]],
                            "D4_exact": [r["B0"]["D4"]["exact"], r[chosen]["D4"]["exact"]], "D4_cer": [r["B0"]["D4"]["cer"], r[chosen]["D4"]["cer"]]},
            "dev_pairs": "all 72 synthetic dev pairs still routed to review (written amounts never parse); baseline identical",
            "p2_adopted": p2["adopt_p2"], "p2_written_cer": [p2["p1_full_line"]["cer"], p2["p2_segmented"]["cer"]],
            "p2_written_value_correct": [p2["p1_full_line"]["value_correct"], p2["p2_segmented"]["value_correct"]],
            "artifacts": sorted(p.name for p in A7.iterdir() if p.is_file()) + ["FROZEN_CONFIG.json", "ABLATION_RESULTS.json", "SUMMARY.json"]}
    for name, obj in (("FROZEN_CONFIG.json", frozen), ("ABLATION_RESULTS.json", abl), ("SUMMARY.json", summ)):
        (A7 / name).write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
