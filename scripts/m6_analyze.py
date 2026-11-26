"""M6 analysis from saved predictions only (no inference). Follows artifacts/M6/EXPERIMENT_PROTOCOL.md.

Inputs : artifacts/M5_DEV/BASELINE_RESULTS.json (clean), artifacts/M6/STRESS_RESULTS.json, artifacts/M6/DIAGNOSTIC_RAW.json,
         data/stress/m6_parents.json, data/diagnostics/m6/*manifest.json, data/benchmarks/amount_pairs.json
Outputs: artifacts/M6/{CLEAN_FAILURE_ANALYSIS, STRESS_METRICS, DIAGNOSTIC_RESULTS, AMOUNT_FAILURE_ANALYSIS}.json + figures/
Usage  : .venv\\Scripts\\python.exe -X utf8 -I scripts\\m6_analyze.py
"""
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import eval_metrics as em  # noqa: E402
import m6_prepare as mp  # noqa: E402
import score_baseline as sb  # noqa: E402

A6 = ROOT / "artifacts/M6"
FIG = A6 / "figures"
SEED, BOOT = 20261126, 1000
CORR, LEVELS = ["lowres", "blur", "illum", "contrast", "noise"], [1, 2, 3]
PUNCT = set(",.-/:()")


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def group_of(r):
    return {"syn_num": "D6_num_SYN", "syn_words": "D6_words_SYN"}.get(r["category"], r["dataset"])


GROUPS = ["D1", "D4", "D5", "D6_num_SYN", "D6_words_SYN"]
GENUINE = {"D1": True, "D4": True, "D5": True, "D6_num_SYN": False, "D6_words_SYN": False}


def ed(r):
    return em.align(sb.pred_of(r), r["ground_truth"])[1]


def exact(r):
    return sb.pred_of(r) == r["ground_truth"]


def value_ok(r):
    v = sb.value_of(r)
    return None if r.get("gt_value") is None else (v is not None and v == Decimal(r["gt_value"]))


def summarize(rows):
    if not rows:
        return {"n": 0}
    tm = em.text_metrics([{"id": r["id"], "gt": r["ground_truth"], "pred": r["prediction"], "error": r["error"]} for r in rows])
    p = tm["primary_failure_aware"]
    vals = [value_ok(r) for r in rows if r.get("gt_value") is not None]
    return {"n": len(rows), "exact": p["exact"], "exact_rate": p["exact_rate"], "cer": p["cer"], "wer": p["wer"],
            "char_edit_distance": p["char_edit_distance"], "gt_chars": p["gt_chars"],
            "punct_precision": p["punctuation"]["precision"], "punct_recall": p["punctuation"]["recall"],
            "value_n": len(vals), "value_exact": sum(bool(v) for v in vals), "failures": tm["failed"],
            "latency": em.latency_stats([r["latency_seconds"] for r in rows if r["latency_seconds"] is not None])}


# ---------------- clean analysis ----------------
def features(r, file):
    rgb = cv2.cvtColor(cv2.imread(str(ROOT / file)), cv2.COLOR_BGR2RGB)
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ink = mp.otsu_ink(grey)
    ys = np.nonzero(ink)[0]
    raw_h, raw_w = grey.shape
    eff_h, eff_w = r["input_shape"][2], r["input_shape"][3]
    ink_h = float(np.percentile(ys, 95) - np.percentile(ys, 5) + 1) * eff_h / raw_h if len(ys) else 0.0
    gt = r["ground_truth"]
    return {"raw_hw": [raw_h, raw_w], "eff_hw": [eff_h, eff_w], "aspect": round(raw_w / raw_h, 3),
            "ink_height_eff": round(ink_h, 1), "occupancy": round(float(ink.mean()), 4),
            "contrast_p95_p5": float(np.percentile(grey, 95) - np.percentile(grey, 5)), "grey_std": round(float(grey.std()), 2),
            "blur_laplacian_var": round(float(cv2.Laplacian(grey, cv2.CV_64F).var()), 1),
            "gt_chars": len(gt), "gt_words": len(gt.split()), "repeated_zero": "00" in gt,
            "repeated_other_digit": any(a == b and a.isdigit() and a != "0" for a, b in zip(gt, gt[1:])),
            "has_digit": any(c.isdigit() for c in gt), "has_punct": any(c in PUNCT for c in gt)}


def bin_of(v, edges, labels):
    for e, lab in zip(edges, labels):
        if v < e:
            return lab
    return labels[-1]


SUBGROUP_RULES = {
    "eff_height_px": lambda f: bin_of(f["eff_hw"][0], [32, 64, 128], ["<32", "32-63", "64-127", ">=128"]),
    "ink_height_px": lambda f: bin_of(f["ink_height_eff"], [12, 24, 48], ["<12", "12-23", "24-47", ">=48"]),
    "gt_length": lambda f: bin_of(f["gt_chars"], [4, 8], ["1-3", "4-7", ">=8"]),
    "repeated_zero": lambda f: f["repeated_zero"], "repeated_other_digit": lambda f: f["repeated_other_digit"],
    "has_digit": lambda f: f["has_digit"], "has_punct": lambda f: f["has_punct"],
    "word_count": lambda f: "multi" if f["gt_words"] > 1 else "single", "genuine": lambda f: f["genuine"],
}


def clean_analysis(clean, parents):
    table = []
    for r in clean:
        f = features(r, parents[r["id"]]["file"])
        f.update({"id": r["id"], "dataset": r["dataset"], "group": group_of(r), "category": r["category"],
                  "genuine": GENUINE[group_of(r)], "ground_truth": r["ground_truth"], "prediction": r["prediction"],
                  "char_edit_distance": ed(r), "exact": exact(r), "value_correct": value_ok(r), "latency": r["latency_seconds"],
                  "failure_categories": sorted(sb.classify(r)) if not exact(r) else []})
        table.append(f)
    by_id = {r["id"]: r for r in clean}
    subgroups = {}
    for name, rule in SUBGROUP_RULES.items():
        buckets = defaultdict(list)
        for f in table:
            buckets[str(rule(f))].append(f)
        out = {}
        for k, fs in sorted(buckets.items()):
            s = summarize([by_id[f["id"]] for f in fs])
            ds = Counter(f["group"] for f in fs)
            top, cnt = ds.most_common(1)[0]
            out[k] = {"n": s["n"], "exact": s["exact"], "cer": s["cer"], "by_group": dict(ds),
                      "inconclusive_n_lt_10": s["n"] < 10,
                      "confounded_with": top if cnt / len(fs) >= 0.8 and len(ds) < len(GROUPS) else None}
        subgroups[name] = out
    within = {}  # the same split inside each group, to separate factor from dataset identity
    for g in GROUPS:
        for name in ("eff_height_px", "ink_height_px", "gt_length"):
            buckets = defaultdict(list)
            for f in table:
                if f["group"] == g:
                    buckets[str(SUBGROUP_RULES[name](f))].append(by_id[f["id"]])
            within[f"{g}:{name}"] = {k: {"n": len(v), "exact": summarize(v)["exact"], "cer": summarize(v)["cer"]}
                                     for k, v in sorted(buckets.items())}
    return table, subgroups, within


# ---------------- stress ----------------
def cluster_boot(pairs, rng):
    """pairs: list of (cluster, ed_clean, ed_var, n_chars, ex_clean, ex_var). 95% CI of dCER and dExact."""
    clusters = defaultdict(list)
    for p in pairs:
        clusters[p[0]].append(p)
    keys = list(clusters)
    if len(keys) < 5:
        return None
    dc, de = [], []
    for _ in range(BOOT):
        sel = [x for k in rng.choice(keys, len(keys), replace=True) for x in clusters[k]]
        n = sum(x[3] for x in sel)
        dc.append((sum(x[2] for x in sel) - sum(x[1] for x in sel)) / n)
        de.append(np.mean([x[5] - x[4] for x in sel]))
    return {"dCER_ci95": [round(float(np.percentile(dc, 2.5)), 4), round(float(np.percentile(dc, 97.5)), 4)],
            "dExact_pp_ci95": [round(100 * float(np.percentile(de, 2.5)), 1), round(100 * float(np.percentile(de, 97.5)), 1)],
            "clusters": len(keys)}


def stress_analysis(clean, stress):
    rng = np.random.default_rng(SEED)
    cmap = {r["id"]: r for r in clean}
    out, trends = {}, {}
    for g in GROUPS:
        base = [r for r in clean if group_of(r) == g]
        out[g] = {"clean": summarize(base)}
        for c in CORR:
            trend = [summarize(base)["cer"]]
            for lv in LEVELS:
                var = [r for r in stress if r["corruption"] == c and r["level"] == lv and group_of(cmap[r["parent_id"]]) == g]
                s = summarize(var)
                par = [cmap[r["parent_id"]] for r in var]
                pc = summarize(par)
                trans = Counter((exact(cmap[r["parent_id"]]), exact(r)) for r in var)
                vtrans = Counter((value_ok(cmap[r["parent_id"]]), value_ok(r)) for r in var if r.get("gt_value") is not None)
                pairs = [(r["group_id"], ed(cmap[r["parent_id"]]), ed(r), len(r["ground_truth"]),
                          int(exact(cmap[r["parent_id"]])), int(exact(r))) for r in var]
                s.update({"paired_clean_cer": pc["cer"], "dCER": round(s["cer"] - pc["cer"], 4),
                          "dExact_pp": round(100 * (s["exact"] - pc["exact"]) / s["n"], 1),
                          "correct_to_wrong": trans[(True, False)], "wrong_to_correct": trans[(False, True)],
                          "value_correct_to_wrong": vtrans[(True, False)], "value_wrong_to_correct": vtrans[(False, True)],
                          "per_sample_ed_increase": sum(1 for p in pairs if p[2] > p[1]),
                          "per_sample_ed_decrease": sum(1 for p in pairs if p[2] < p[1]),
                          "bootstrap": cluster_boot(pairs, rng) if g != "D5" else "n too small"})
                out[g][f"{c}_s{lv}"] = s
                trend.append(s["cer"])
            trends[f"{g}:{c}"] = {"cer_clean_s1_s2_s3": [round(x, 4) for x in trend],
                                  "monotonic_nondecreasing": all(b >= a for a, b in zip(trend, trend[1:]))}
    return out, trends


# ---------------- diagnostics ----------------
def joined(rows):
    """Join word predictions in word order; any failed word -> empty word."""
    rows = sorted(rows, key=lambda r: r["id"])  # ids end in zero-padded _wNN = word order
    return " ".join(sb.pred_of(r) for r in rows)


def text_score(pred, gt, gt_value, category):
    e = em.align(pred, gt)[1]
    v = em.words_value(pred) if category in sb.WORD_CATS else em.numeric_value(pred)
    return {"exact": pred == gt, "ed": e, "chars": len(gt), "parseable": v is not None,
            "value_exact": v is not None and gt_value is not None and v == Decimal(gt_value)}


def agg(scores):
    n = len(scores)
    return {"n": n, "exact": sum(s["exact"] for s in scores), "cer": round(sum(s["ed"] for s in scores) / max(1, sum(s["chars"] for s in scores)), 4),
            "parseable": sum(s["parseable"] for s in scores), "value_exact": sum(s["value_exact"] for s in scores)}


def diagnostics(clean, diag_rows, diag_man, parents):
    cmap = {r["id"]: r for r in clean}
    dmeta = {d["id"]: d for d in diag_man}
    res = {}
    # DX-A pipeline sanity
    pol, ranges, eff_ok, tok = [], [], 0, set()
    for r in clean:
        rgb = cv2.cvtColor(cv2.imread(str(ROOT / parents[r["id"]]["file"])), cv2.COLOR_BGR2RGB)
        grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        ink = mp.otsu_ink(grey)
        pol.append(bool(grey[~ink].mean() > grey[ink].mean()) if ink.any() and (~ink).any() else None)
        ranges.append((int(rgb.min()), int(rgb.max())))
        eff_ok += mp.effective_hw(rgb) == r["input_shape"][2:]
        tok |= set(r["raw_token_ids"] or [])
    res["DX-A"] = {"n": len(clean), "dark_ink_on_light_background": sum(1 for p in pol if p), "polarity_undetermined": pol.count(None),
                   "uint8_range_0_255": all(0 <= a <= b <= 255 for a, b in ranges),
                   "pixel_scaling": "ToTensor divides by 255 (upstream); RGB channel order via PIL convert('RGB')",
                   "effective_dims_match_upstream_ScaleToLimitRange": f"{eff_ok}/{len(clean)}",
                   "token_id_range": [min(tok), max(tok)], "vocab_size": 97,
                   "decoder": "beam 10, max_len 200, alpha 1.0 (checkpoint hyper-parameters, unchanged)",
                   "crop_alignment": "amount fields verified visually in M4-ONLINE/M4-FINAL; DX-C/DX-D crops viewed (AI check)"}
    # DX-B resolution
    dxb = {}
    for sub, sel in (("D1", lambda p: p["dataset"] == "D1"), ("D4", lambda p: p["dataset"] == "D4"),
                     ("D6_num_SYN", lambda p: p["category"] == "syn_num"), ("D6_words_SYN", lambda p: p["category"] == "syn_words")):
        ids = [i for i in diag_man_subsets["DX-B"] if sel(cmap[i])]
        cond = {"orig": [text_score(sb.pred_of(cmap[i]), cmap[i]["ground_truth"], cmap[i].get("gt_value"), cmap[i]["category"]) for i in ids]}
        eff = {"orig": [cmap[i]["input_shape"][2] for i in ids]}
        for k in (2, 4):
            rows = [r for r in diag_rows if dmeta[r["id"]]["condition"] == f"DXB_up{k}" and r["parent_id"] in ids]
            cond[f"up{k}"] = [text_score(sb.pred_of(r), r["ground_truth"], r.get("gt_value"), r["category"]) for r in rows]
            eff[f"up{k}"] = [dmeta[r["id"]]["effective_hw"][0] for r in rows]
        dxb[sub] = {c: {**agg(v), "median_effective_height": float(np.median(eff[c]))} for c, v in cond.items()}
    res["DX-B"] = dxb
    # DX-C multiword
    dxc = {}
    ids = diag_man_subsets["DX-C"]
    up2 = {r["parent_id"]: r for r in diag_rows if dmeta[r["id"]]["condition"] == "DXB_up2"}
    conds = {"full_1x": {i: sb.pred_of(cmap[i]) for i in ids}, "full_2x": {i: sb.pred_of(up2[i]) for i in ids}}
    for prefix in ("DXC_seg1x", "DXC_seg2x", "DXC_oracle1x", "DXC_oracle2x"):
        conds[prefix.replace("DXC_", "")] = {i: joined([r for r in diag_rows if r["parent_id"] == i and dmeta[r["id"]]["condition"].startswith(prefix)]) for i in ids}
    for c, preds in conds.items():
        sc = [text_score(preds[i], cmap[i]["ground_truth"], cmap[i].get("gt_value"), "syn_words") for i in ids]
        dxc[c] = {**agg(sc), "wer": round(sum(em.align(preds[i].split(), cmap[i]["ground_truth"].split())[1] for i in ids)
                                          / sum(len(cmap[i]["ground_truth"].split()) for i in ids), 4),
                  "examples": {i: preds[i] for i in ids[:3]}}
    word_exact = {}
    for k in (1, 2):
        ws = [r for r in diag_rows if dmeta[r["id"]]["condition"] == f"DXC_oracle{k}x"]
        word_exact[f"oracle{k}x"] = {"words": len(ws), "exact_words": sum(1 for r in ws if sb.pred_of(r) == r["ground_truth"].split()[dmeta[r["id"]]["word_index"]])}
    dxc["per_word_oracle"] = word_exact
    dxc["geometric_segmentation_matched_word_count"] = f"{sum(1 for i in ids if any(d['parent_id'] == i and d.get('segmentation_matches_gt_count') for d in diag_man))}/{len(ids)}"
    res["DX-C"] = dxc
    # DX-D contamination
    dxd = {}
    for cat in ("syn_num", "syn_words"):
        ids = [i for i in diag_man_subsets["DX-D"] if cmap[i]["category"] == cat]
        out = {"orig1x": agg([text_score(sb.pred_of(cmap[i]), cmap[i]["ground_truth"], cmap[i].get("gt_value"), cat) for i in ids])}
        for c in ("DXD_orig2x", "DXD_clean1x", "DXD_clean2x"):
            rows = [r for r in diag_rows if dmeta[r["id"]]["condition"] == c and r["parent_id"] in ids]
            out[c.replace("DXD_", "")] = agg([text_score(sb.pred_of(r), r["ground_truth"], r.get("gt_value"), cat) for r in rows])
        out["removed_pixels_median"] = float(np.median([dmeta[d]["removed_pixels"] for d in dmeta if dmeta[d]["condition"] == "DXD_clean1x" and dmeta[d]["parent_id"] in ids]))
        dxd[cat] = out
    res["DX-D"] = dxd
    return res


def punct_digit_analysis(rows):
    """DX-E counts over value-bearing or digit-containing ground truths."""
    c = Counter()
    ratios = []
    for r in rows:
        gt = r["ground_truth"]
        if not any(ch.isdigit() for ch in gt):
            continue
        for op, p, g in em.align(sb.pred_of(r), gt)[0]:
            if op == "extra" and p == "0":
                c["zero_insertions"] += 1
            elif op == "missing" and g == "0":
                c["zero_deletions"] += 1
            elif op == "sub" and p and g and p.isdigit() and g.isdigit():
                c["digit_substitutions"] += 1
            elif g == "," and op != "match":
                c["comma_missing_or_wrong"] += 1
            elif g == "." and op != "match":
                c["decimal_missing_or_wrong"] += 1
            elif op == "sub" and g in PUNCT and p in PUNCT:
                c["punct_substitutions"] += 1
        gv = em.numeric_value(gt)
        pv = em.numeric_value(sb.pred_of(r))
        if gv and pv:
            ratios.append(float(pv / gv))
    rr = np.array(ratios) if ratios else np.array([1.0])
    return {"digit_bearing_samples": sum(1 for r in rows if any(ch.isdigit() for ch in r["ground_truth"])), **dict(c),
            "value_parsed_both": len(ratios), "value_exact": int((rr == 1).sum()) if ratios else 0,
            "value_off_by_10x_or_more": int(((rr >= 10) | (rr <= 0.1)).sum()) if ratios else 0,
            "value_within_10pct_but_wrong": int(((rr != 1) & (abs(rr - 1) < 0.1)).sum()) if ratios else 0}


# ---------------- amount pairs ----------------
def pair_reason(n, w, label):
    if label == "unresolved":
        return "blank_source_field"
    nv, wv = sb.value_of(n) if n else None, sb.value_of(w) if w else None
    if nv is None and wv is None:
        return "both_unparseable"
    if nv is None:
        return "numeric_unparseable"
    if wv is None:
        return "written_unparseable"
    return "correct" if (nv == Decimal(n["gt_value"]) and wv == Decimal(w["gt_value"])) else "parsed_but_wrong_value"


def amount_analysis(clean, stress):
    cmap = {r["id"]: r for r in clean}
    smap = {r["id"]: r for r in stress}
    pairs = [p for p in load("data/benchmarks/amount_pairs.json")["pairs"] if p["split"] == "dev"]
    clean_out = []
    for p in pairs:
        n, w = cmap.get(p["num_id"]), cmap.get(p["words_id"])
        dec = em.decide(sb.value_of(n) if n else None, sb.value_of(w) if w else None)
        clean_out.append({"pair_id": p["pair_id"], "dataset": p["dataset"], "construction": p["construction"], "label": p["label"],
                          "decision": dec, "reason": pair_reason(n, w, p["label"])})
    def cov(items):
        elig = [x for x in items if x["label"] in ("match", "mismatch")]
        m = em.discrepancy_metrics([{"id": x["pair_id"], "label": x["label"], "decision": x["decision"]} for x in items])
        return {"pairs": len(items), "resolved": len(elig), "unresolved": len(items) - len(elig),
                "auto_accept_coverage_of_matches": f"{sum(1 for x in elig if x['label'] == 'match' and x['decision'] == 'accept')}/{sum(1 for x in elig if x['label'] == 'match')}",
                "auto_flag_coverage_of_mismatches": f"{sum(1 for x in elig if x['label'] == 'mismatch' and x['decision'] == 'flag')}/{sum(1 for x in elig if x['label'] == 'mismatch')}",
                "review_rate": m["manual_review_rate"], "incorrect_acceptance_rate": m["incorrect_acceptance_rate"],
                "incorrect_rejection_rate": m["incorrect_rejection_rate"], "all_review": m["all_review"],
                "reasons": dict(Counter(x["reason"] for x in items))}
    summary = {ds: cov([x for x in clean_out if x["dataset"] == ds]) for ds in ("gnhk_pairs", "syn_cheques")}
    stress_out = {}
    for c in CORR:
        for lv in LEVELS:
            items = []
            for p in pairs:
                n, w = smap.get(f"{p['num_id']}__{c}_s{lv}"), smap.get(f"{p['words_id']}__{c}_s{lv}")
                items.append({"pair_id": p["pair_id"], "dataset": p["dataset"], "label": p["label"],
                              "decision": em.decide(sb.value_of(n) if n else None, sb.value_of(w) if w else None),
                              "reason": pair_reason(n, w, p["label"])})
            stress_out[f"{c}_s{lv}"] = {ds: cov([x for x in items if x["dataset"] == ds]) for ds in ("gnhk_pairs", "syn_cheques")}
    return {"note": "constructed pairs reuse field crops; pairs are not independent observations", "clean": summary,
            "clean_pairs": clean_out, "stress": stress_out}


# ---------------- figures ----------------
def figures(stress_m, table, diag, clean, stress):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIG.mkdir(parents=True, exist_ok=True)
    gplot = ["D1", "D4", "D6_num_SYN", "D6_words_SYN"]
    titles = {"D1": "D1 GNHK words (genuine)", "D4": "D4 CVL digits (genuine)", "D6_num_SYN": "D6 numeric (synthetic)",
              "D6_words_SYN": "D6 words (synthetic)"}
    for metric, fname, ylab in (("cer", "cer_vs_severity.png", "aggregate CER"), ("exact_rate", "exact_vs_severity.png", "exact match rate")):
        fig, axes = plt.subplots(1, 4, figsize=(16, 3.8), sharey=(metric == "exact_rate"))
        for ax, g in zip(axes, gplot):
            for c in CORR:
                ys = [stress_m[g]["clean"][metric]] + [stress_m[g][f"{c}_s{l}"][metric] for l in LEVELS]
                ax.plot([0, 1, 2, 3], ys, marker="o", label=c)
            ax.set_title(titles[g], fontsize=10)
            ax.set_xticks([0, 1, 2, 3], ["clean", "1", "2", "3"])
            ax.set_xlabel("severity level")
            ax.grid(alpha=0.3)
        axes[0].set_ylabel(ylab)
        axes[-1].legend(fontsize=8)
        fig.suptitle(f"{ylab} by corruption and severity (dev, n = clean parents per panel)", fontsize=11)
        fig.tight_layout()
        fig.savefig(FIG / fname, dpi=150)
        plt.close(fig)
    cols = [f"{c}_s{l}" for c in CORR for l in LEVELS]
    mat = np.array([[stress_m[g][k]["dCER"] for k in cols] for g in gplot])
    fig, ax = plt.subplots(figsize=(14, 3.2))
    im = ax.imshow(mat, cmap="Reds", aspect="auto")
    ax.set_xticks(range(len(cols)), cols, rotation=60, fontsize=8)
    ax.set_yticks(range(len(gplot)), [titles[g] for g in gplot], fontsize=9)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:+.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, label="CER change vs clean (paired)")
    ax.set_title("Paired CER degradation per corruption level (dev)")
    fig.tight_layout()
    fig.savefig(FIG / "degradation_heatmap.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for g, mk in zip(GROUPS, "o^sDv"):
        fs = [f for f in table if f["group"] == g]
        ax.scatter([f["ink_height_eff"] for f in fs], [f["char_edit_distance"] / max(1, f["gt_chars"]) for f in fs], s=14, marker=mk, label=g, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("estimated ink height after upstream transform (px, log)")
    ax.set_ylabel("per-sample CER")
    ax.set_title("Clean dev error vs effective ink height")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "error_vs_geometry.png", dpi=150)
    plt.close(fig)
    cats = Counter()
    by = defaultdict(Counter)
    for f in table:
        for c in f["failure_categories"]:
            cats[c] += 1
            by[c][f["group"]] += 1
    names = [c for c, _ in cats.most_common()]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    bottom = np.zeros(len(names))
    for g in GROUPS:
        vals = np.array([by[c][g] for c in names])
        ax.bar(names, vals, bottom=bottom, label=g)
        bottom += vals
    ax.set_ylabel("samples (multi-label)")
    ax.set_title("Clean dev error categories")
    ax.tick_params(axis="x", rotation=55, labelsize=8)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "error_categories.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    b = diag["DX-B"]
    x = np.arange(4)
    for j, c in enumerate(("orig", "up2", "up4")):
        axes[0].bar(x + j * 0.27, [b[g][c]["cer"] for g in gplot], 0.27, label=c)
    axes[0].set_xticks(x + 0.27, [g.replace("_SYN", "") for g in gplot], fontsize=8)
    axes[0].set_title("DX-B resolution (CER, n=8 each)")
    axes[0].legend(fontsize=8)
    cc = diag["DX-C"]
    keys = ["full_1x", "full_2x", "seg1x", "seg2x", "oracle1x", "oracle2x"]
    axes[1].bar(keys, [cc[k]["cer"] for k in keys], color="tab:purple")
    axes[1].set_title("DX-C multiword lines (CER, n=8)")
    axes[1].tick_params(axis="x", rotation=40, labelsize=8)
    d = diag["DX-D"]
    keys = ["orig1x", "orig2x", "clean1x", "clean2x"]
    for j, cat in enumerate(("syn_num", "syn_words")):
        axes[2].bar(np.arange(4) + j * 0.4, [d[cat][k]["cer"] for k in keys], 0.4, label=cat)
    axes[2].set_xticks(np.arange(4) + 0.2, keys, fontsize=8)
    axes[2].set_title("DX-D line removal (CER, n=8 each)")
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.set_ylabel("CER")
        ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "diagnostics.png", dpi=150)
    plt.close(fig)
    # qualitative examples by rule: largest paired ED increase per group at severity 3 (ties -> sorted id)
    cmap = {r["id"]: r for r in clean}
    rows_out = []
    for g in gplot:
        cand = [r for r in stress if r["level"] == 3 and group_of(cmap[r["parent_id"]]) == g]
        cand.sort(key=lambda r: (-(ed(r) - ed(cmap[r["parent_id"]])), r["id"]))
        rows_out += cand[:2]
    fig, axes = plt.subplots(len(rows_out), 2, figsize=(11, 1.5 * len(rows_out)))
    parents = {p["id"]: p for p in load("data/stress/m6_parents.json")["samples"]}
    vman = {v["id"]: v for v in load("data/stress/m6_dev/manifest.json")["samples"]}
    for i, r in enumerate(rows_out):
        p = cmap[r["parent_id"]]
        for j, (path, pred, tag) in enumerate(((parents[p["id"]]["file"], p["prediction"], "clean"), (vman[r["id"]]["file"], r["prediction"], f"{r['corruption']} s3"))):
            ax = axes[i, j]
            ax.imshow(cv2.cvtColor(cv2.imread(str(ROOT / path)), cv2.COLOR_BGR2RGB))
            ax.set_title(f"{p['id']} [{tag}] GT={p['ground_truth'][:30]!r} pred={str(pred)[:30]!r}", fontsize=7)
            ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIG / "examples_largest_paired_errors.png", dpi=130)
    plt.close(fig)
    return [p.name for p in sorted(FIG.glob("*.png"))]


diag_man_subsets = {}


def main():
    outs = ["CLEAN_FAILURE_ANALYSIS.json", "STRESS_METRICS.json", "DIAGNOSTIC_RESULTS.json", "AMOUNT_FAILURE_ANALYSIS.json"]
    for o in outs:
        if (A6 / o).exists():
            raise SystemExit(f"{A6 / o} exists; refusing to overwrite")
    clean = [r for r in load("artifacts/M5_DEV/BASELINE_RESULTS.json")["results"] if r["recognition_eligible"]]
    assert len(clean) == 245 and all(r["split"] == "dev" for r in clean)
    parents = {p["id"]: p for p in load("data/stress/m6_parents.json")["samples"]}
    stress = load("artifacts/M6/STRESS_RESULTS.json")["results"]
    assert len(stress) == 15 * len(clean) and {r["parent_id"] for r in stress} == {r["id"] for r in clean}
    dm = load("data/diagnostics/m6/manifest.json")
    diag_man = dm["samples"] + load("data/diagnostics/m6/dxc_oracle_manifest.json")["samples"]
    diag_man_subsets.update(dm["subsets"])
    diag_rows = load("artifacts/M6/DIAGNOSTIC_RAW.json")["results"]
    assert {r["id"] for r in diag_rows} == {d["id"] for d in diag_man}

    table, subgroups, within = clean_analysis(clean, parents)
    stress_m, trends = stress_analysis(clean, stress)
    diag = diagnostics(clean, diag_rows, diag_man, parents)
    diag["DX-E"] = {"clean": punct_digit_analysis(clean),
                    "stress_by_corruption": {c: punct_digit_analysis([r for r in stress if r["corruption"] == c]) for c in CORR}}
    amount = amount_analysis(clean, stress)
    (A6 / "CLEAN_FAILURE_ANALYSIS.json").write_text(json.dumps({"rules": "artifacts/M6/EXPERIMENT_PROTOCOL.md", "per_sample": table,
                                                                "subgroups": subgroups, "within_group": within}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (A6 / "STRESS_METRICS.json").write_text(json.dumps({"groups": stress_m, "severity_trends": trends}, indent=1, default=str), encoding="utf-8")
    (A6 / "DIAGNOSTIC_RESULTS.json").write_text(json.dumps(diag, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (A6 / "AMOUNT_FAILURE_ANALYSIS.json").write_text(json.dumps(amount, indent=1, default=str), encoding="utf-8")
    figs = figures(stress_m, table, diag, clean, stress)
    print("figures:", figs)
    for g in GROUPS:
        print(g, "clean", round(stress_m[g]["clean"]["cer"], 3), {k: (round(v["cer"], 3), v["dExact_pp"]) for k, v in stress_m[g].items() if k != "clean"})
    print(json.dumps({k: v for k, v in subgroups.items()}, default=str)[:3000])
    print(json.dumps(diag, default=str)[:4000])
    print(json.dumps(amount["clean"], default=str))


if __name__ == "__main__":
    main()
