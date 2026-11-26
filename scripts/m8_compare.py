"""M8: compare baseline and frozen proposed method on the locked test split (identical inputs). Reads saved runs only.
Inputs: artifacts/M8/runs/{baseline,proposed}/ (BASELINE_RESULTS.json scored by score_baseline.py --split test).
Paired statistics: cluster bootstrap over group_id (10,000 resamples, seed 20261126) for aggregate-CER and exact
differences; exact two-sided McNemar (binomial) on discordant items.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m8_compare.py
"""
import json
import math
import random
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eval_metrics as em  # noqa: E402
import score_baseline as sb  # noqa: E402

A8 = ROOT / "artifacts/M8"
RUNS = {m: A8 / "runs" / m for m in ("baseline", "proposed")}
GROUPS = {("D1", None): "D1_gnhk_words_genuine", ("D4", None): "D4_cvl_numeric_genuine",
          ("D5", "gnhk_numeric"): "D5_gnhk_numeric_genuine", ("D5", "gnhk_word"): "D5_gnhk_words_genuine",
          ("D6", "syn_num"): "D6_syn_numeric_SYNTHETIC", ("D6", "syn_words"): "D6_syn_words_SYNTHETIC"}
B, SEED = 10000, 20261126


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def gkey(r):
    return GROUPS.get((r["dataset"], None)) or GROUPS[(r["dataset"], r["category"])]


def item(r):
    pred = "" if sb.failed(r) else r["prediction"]
    v = sb.value_of(r) if r.get("gt_value") is not None else None
    return {"ed": em.align(pred, r["ground_truth"])[1], "n": len(r["ground_truth"]), "exact": int(pred == r["ground_truth"]),
            "value": None if r.get("gt_value") is None else int(v is not None and v == Decimal(r["gt_value"])),
            "group": r.get("group_id") or r["id"]}


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def paired(base, prop, rng):
    """base/prop: aligned item lists. Returns deltas (proposed - baseline) with cluster-bootstrap 95% CIs."""
    clusters = defaultdict(list)
    for a, b in zip(base, prop):
        clusters[a["group"]].append((a, b))
    keys = sorted(clusters)

    def stats(sample):
        ed_a = sum(a["ed"] for a, _ in sample); ed_b = sum(b["ed"] for _, b in sample); n = sum(a["n"] for a, _ in sample)
        return (ed_b - ed_a) / n if n else 0.0, sum(b["exact"] - a["exact"] for a, b in sample)
    obs = stats([p for k in keys for p in clusters[k]])
    boots = []
    for _ in range(B):
        boots.append(stats([p for k in (rng.choice(keys) for _ in keys) for p in clusters[k]]))
    ci = lambda xs: [round(sorted(xs)[int(0.025 * B)], 4), round(sorted(xs)[int(0.975 * B) - 1], 4)]
    out = {"n_items": len(base), "n_clusters": len(keys),
           "cer_delta": round(obs[0], 4), "cer_delta_ci95": ci([x[0] for x in boots]),
           "exact_delta": obs[1], "exact_delta_ci95": ci([x[1] for x in boots]),
           "exact_mcnemar": {"improved": sum(1 for a, b in zip(base, prop) if b["exact"] > a["exact"]),
                             "regressed": sum(1 for a, b in zip(base, prop) if b["exact"] < a["exact"])}}
    em_ = out["exact_mcnemar"]
    em_["p_value"] = float(f"{mcnemar(em_['improved'], em_['regressed']):.3g}")
    vb = [(a, b) for a, b in zip(base, prop) if a["value"] is not None]
    if vb:
        imp, reg = sum(1 for a, b in vb if b["value"] > a["value"]), sum(1 for a, b in vb if b["value"] < a["value"])
        out["value_mcnemar"] = {"n": len(vb), "improved": imp, "regressed": reg, "p_value": float(f"{mcnemar(imp, reg):.3g}")}
    return out


def dataset_table(mb, mp):
    rows = {}
    for g in GROUPS.values():
        a, b = mb[g]["primary_failure_aware"], mp[g]["primary_failure_aware"]
        n = a["n"]
        row = {"n_eligible": n, "blank_fields": mb[g]["blank_fields"]}
        for k in ("cer", "wer", "exact_rate"):
            row[k] = {"baseline": round(a[k], 4), "proposed": round(b[k], 4), "delta": round(b[k] - a[k], 4)}
        row["exact"] = {"baseline": a["exact"], "proposed": b["exact"]}
        row["exact_rate"]["delta_pp"] = round(100 * (b["exact_rate"] - a["exact_rate"]), 1)
        row["relative_cer_reduction"] = round((a["cer"] - b["cer"]) / a["cer"], 4) if a["cer"] else None
        row["punctuation"] = {m: {k: x["punctuation"][k] for k in ("precision", "recall")} for m, x in (("baseline", a), ("proposed", b))}
        row["coverage"] = {"baseline": mb[g]["coverage"], "proposed": mp[g]["coverage"]}
        row["failure_rate"] = {"baseline": mb[g]["failed"] / n, "proposed": mp[g]["failed"] / n}
        if "amount_value" in mb[g]:
            va, vp = mb[g]["amount_value"], mp[g]["amount_value"]
            row["value_exact"] = {"n": va["n"], "baseline": va["exact"], "proposed": vp["exact"],
                                  "delta_pp": round(100 * (vp["exact"] - va["exact"]) / va["n"], 1),
                                  "parseable": {"baseline": va["parseable"], "proposed": vp["parseable"]}}
        rows[g] = row
    return rows


def pair_table(pb, pp):
    out = {}
    for k in pb["metrics"]:
        a, b = pb["metrics"][k], pp["metrics"][k]
        out[k] = {m: {"n_eligible": x["n_eligible"], "unresolved": len(x["unresolved_excluded"]), "confusion": x["confusion"],
                      "decisions": x["decisions"], "incorrect_acceptance_rate": x["incorrect_acceptance_rate"],
                      "incorrect_rejection_rate": x["incorrect_rejection_rate"], "review_rate": x["manual_review_rate"],
                      "decision_coverage": None if x["manual_review_rate"] is None else round(1 - x["manual_review_rate"], 4),
                      "explicit_mismatch_detection": x["confusion"].get("mismatch->flag"),
                      "flag_or_review_prf": x["primary_flag_or_review_positive"], "decided_only": x["secondary_decided_only"],
                      "auto_accepted_matches": x["confusion"].get("match->accept"), "all_review": x["all_review"]}
                  for m, x in (("baseline", a), ("proposed", b))}
    return out


def figures(table, pairs, stats, rt):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir = A8 / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    names = list(table)
    short = [n.replace("_SYNTHETIC", " (syn)").replace("_genuine", "") for n in names]
    x = range(len(names))
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
    for j, (key, lab) in enumerate((("cer", "aggregate CER (failure-aware)"), ("exact_rate", "exact-match rate"))):
        ax[j].bar([i - 0.2 for i in x], [table[n][key]["baseline"] for n in names], 0.4, label="baseline")
        ax[j].bar([i + 0.2 for i in x], [table[n][key]["proposed"] for n in names], 0.4, label="proposed (ATHN)")
        ax[j].set_xticks(list(x), short, rotation=30, ha="right", fontsize=8)
        ax[j].set_title(f"{lab}, locked test split")
        ax[j].grid(axis="y", alpha=0.3)
    ax[0].legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "test_cer_exact.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    d = [stats[n]["cer_delta"] for n in names]
    lo = [stats[n]["cer_delta"] - stats[n]["cer_delta_ci95"][0] for n in names]
    hi = [stats[n]["cer_delta_ci95"][1] - stats[n]["cer_delta"] for n in names]
    ax.errorbar(list(x), d, yerr=[lo, hi], fmt="o", capsize=4)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(list(x), short, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("CER(proposed) - CER(baseline)")
    ax.set_title("Paired CER change, 95% cluster-bootstrap CI (test)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(fig_dir / "test_cer_delta_ci.png", dpi=150)
    plt.close(fig)
    subsets = [k for k in pairs if pairs[k]["baseline"]["n_eligible"]]
    fig, ax = plt.subplots(1, len(subsets), figsize=(4.2 * len(subsets), 4), squeeze=False)
    for j, k in enumerate(subsets):
        for i, m in enumerate(("baseline", "proposed")):
            bottom = 0
            for dname, col in (("accept", "tab:green"), ("flag", "tab:red"), ("review", "tab:gray")):
                v = pairs[k][m]["decisions"].get(dname, 0)
                ax[0][j].bar(i, v, 0.6, bottom=bottom, color=col, label=dname if (i, j) == (0, 0) else None)
                bottom += v
        ax[0][j].set_xticks([0, 1], ["baseline", "proposed"])
        ax[0][j].set_title(k, fontsize=9)
    ax[0][0].set_ylabel("pairs")
    ax[0][0].legend(fontsize=8)
    fig.suptitle("Amount-pair decisions on the locked test split (all pairs incl. unresolved)")
    fig.tight_layout()
    fig.savefig(fig_dir / "test_pair_decisions.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot([rt["baseline"], rt["proposed"]], showfliers=True)
    ax.set_xticks([1, 2], ["baseline", "proposed"])
    ax.set_yscale("log")
    ax.set_ylabel("per-input inference latency (s, log)")
    ax.set_title("Latency per unique test input (CPU)")
    fig.tight_layout()
    fig.savefig(fig_dir / "test_latency.png", dpi=150)
    plt.close(fig)


def main():
    res = {m: load(RUNS[m] / "BASELINE_RESULTS.json") for m in RUNS}
    rows = {m: {r["id"]: r for r in res[m]["results"]} for m in RUNS}
    assert rows["baseline"].keys() == rows["proposed"].keys()
    assert all(rows["baseline"][i]["input_sha256"] == rows["proposed"][i]["input_sha256"] for i in rows["baseline"])
    elig = sorted(i for i, r in rows["baseline"].items() if r["recognition_eligible"])
    mb, mp = (load(RUNS[m] / "METRICS.json")["groups"] for m in RUNS)
    pb, pp = (load(RUNS[m] / "PAIR_RESULTS.json") for m in RUNS)
    table = dataset_table(mb, mp)
    rng = random.Random(SEED)
    stats = {}
    for g in GROUPS.values():
        ids = [i for i in elig if gkey(rows["baseline"][i]) == g]
        stats[g] = paired([item(rows["baseline"][i]) for i in ids], [item(rows["proposed"][i]) for i in ids], rng)
    gen = [i for i in elig if rows["baseline"][i]["dataset"] in ("D1", "D4", "D5")]
    stats["ALL_GENUINE"] = paired([item(rows["baseline"][i]) for i in gen], [item(rows["proposed"][i]) for i in gen], rng)
    pairs = pair_table(pb, pp)
    pidx = {m: {p["pair_id"]: p for p in x["pairs"]} for m, x in (("baseline", pb), ("proposed", pp))}
    ok = lambda p: (p["label"], p["decision"]) in (("match", "accept"), ("mismatch", "flag"))
    lab = [k for k, p in pidx["baseline"].items() if p["label"] in ("match", "mismatch")]
    imp = sum(1 for k in lab if ok(pidx["proposed"][k]) and not ok(pidx["baseline"][k]))
    reg = sum(1 for k in lab if ok(pidx["baseline"][k]) and not ok(pidx["proposed"][k]))
    stats["PAIRS_correct_automatic_decision"] = {"n_labelled": len(lab), "improved": imp, "regressed": reg, "p_value": float(f"{mcnemar(imp, reg):.3g}")}
    lat = {m: [r["latency_seconds"] for r in res[m]["results"] if r["latency_seconds"] is not None] for m in RUNS}
    pre = [r["preprocess"].get("preprocess_seconds", 0) for r in res["proposed"]["results"] if r.get("preprocess")]
    runtime = {m: {**em.latency_stats(lat[m]), "computed_this_run": res[m]["run"]["computed_this_run"],
                   "wall_seconds": res[m]["run"]["wall_seconds"]} for m in RUNS}
    runtime["proposed_preprocess_overhead"] = em.latency_stats(pre)
    runtime["resized_by_proposed"] = res["proposed"]["run"]["resized"]
    runtime["note"] = "latency = model forward + beam search per unique input; reused-cache rows keep their original latency"
    regress = {g: {"exact_regressions": stats[g]["exact_mcnemar"]["regressed"], "exact_improvements": stats[g]["exact_mcnemar"]["improved"]}
               for g in GROUPS.values()}
    (A8 / "COMPARATIVE_METRICS.json").write_text(json.dumps({"split": "test", "datasets": table, "pairs": pairs,
                                                             "improvements_vs_regressions": regress,
                                                             "proposed_config": res["proposed"]["run"]["config"]}, indent=1), encoding="utf-8")
    (A8 / "STATISTICAL_ANALYSIS.json").write_text(json.dumps({"method": f"cluster bootstrap over group_id, B={B}, seed={SEED}; "
                                                              "exact two-sided McNemar (binomial) on discordant items; no multiplicity "
                                                              "correction (descriptive, report-level)", "results": stats}, indent=1), encoding="utf-8")
    (A8 / "RUNTIME_REPORT.json").write_text(json.dumps(runtime, indent=1), encoding="utf-8")
    figures(table, pairs, stats, lat)
    print(json.dumps({g: {"cer": table[g]["cer"], "exact": table[g]["exact"], "value": table[g].get("value_exact", {}),
                          "ci": stats[g]["cer_delta_ci95"], "mcn": stats[g]["exact_mcnemar"]} for g in table}, indent=1))
    print(json.dumps({k: {m: v[m]["decisions"] for m in v} for k, v in pairs.items()}))
    print(json.dumps(stats["PAIRS_correct_automatic_decision"]), json.dumps({m: runtime[m]["median"] for m in RUNS}))


if __name__ == "__main__":
    main()
