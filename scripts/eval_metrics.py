"""Frozen evaluation metrics for ChequeVerify (M4; amended M4-AUDIT 2026-11-26, before any formal evaluation).

See artifacts/M4/EVALUATION_PROTOCOL.md. Key rules:
- Failure-aware: any record with an error, or with a missing/None prediction, counts as an EMPTY prediction
  in primary metrics (edit distance = len(gt)), even if a stale prediction string is present.
  Success-only metrics and coverage are reported separately. Records without ground truth are not eligible.
- Aggregate CER = sum(char edit distance) / sum(len(gt)); WER = sum(word edit distance) / sum(#gt words).
- Punctuation is scored by character alignment (deterministic Levenshtein backtrace); rows flagged
  punct_eligible=False (ambiguous marks) are excluded and listed. Alignment under minimum edit distance is
  a defined matching rule, not proof of absolute positional correctness.
- Amount values use strict grammars (numeric_value, words_value); malformed input -> None -> manual review.
Tests: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m4_audit.py
"""
import math
import re
import statistics
from decimal import Decimal

PUNCT = set(",.-/")


def align(a, b):
    """Levenshtein alignment of pred a to gt b -> (ops, distance); ops are (op, a_item|None, b_item|None).
    Tie-break: match/substitute, then extra (pred item), then missing (gt item). Works on str or list."""
    n, m = len(a), len(b)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j - 1] + (a[i - 1] != b[j - 1]), d[i - 1][j] + 1, d[i][j - 1] + 1)
    ops, i, j = [], n, m
    while i or j:
        if i and j and d[i][j] == d[i - 1][j - 1] + (a[i - 1] != b[j - 1]):
            ops.append(("match" if a[i - 1] == b[j - 1] else "sub", a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i and d[i][j] == d[i - 1][j] + 1:
            ops.append(("extra", a[i - 1], None))
            i -= 1
        else:
            ops.append(("missing", None, b[j - 1]))
            j -= 1
    return ops[::-1], d[n][m]


def punct_counts(pred: str, gt: str):
    """(tp, fp, fn) for punctuation marks under the alignment above."""
    ops, _ = align(pred, gt)
    tp = sum(1 for op, p, g in ops if op == "match" and g in PUNCT)
    fn = sum(1 for op, p, g in ops if g in PUNCT and op != "match")
    fp = sum(1 for op, p, g in ops if p in PUNCT and op != "match")
    return tp, fp, fn


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f}


def _failed(r) -> bool:
    return bool(r.get("error")) or r.get("pred") is None


def text_metrics(rows):
    """rows: dicts with 'gt' and optionally 'pred', 'error', 'id', 'punct_eligible' (default True)."""
    eligible = [r for r in rows if isinstance(r.get("gt"), str) and r["gt"] != ""]
    no_gt = [r.get("id") for r in rows if r not in eligible]

    def agg(rs, failure_aware):
        ced = cn = wed = wn = ex = 0
        tp = fp = fn = 0
        punct_rows = 0
        for r in rs:
            pred = "" if (failure_aware and _failed(r)) else r["pred"]
            ced += align(pred, r["gt"])[1]
            cn += len(r["gt"])
            gw = r["gt"].split()
            wed += align(pred.split(), gw)[1]
            wn += len(gw)
            ex += pred == r["gt"]
            if r.get("punct_eligible", True):
                punct_rows += 1
                t = punct_counts(pred, r["gt"])
                tp, fp, fn = tp + t[0], fp + t[1], fn + t[2]
        return {"n": len(rs), "exact": ex, "exact_rate": ex / len(rs) if rs else None,
                "char_edit_distance": ced, "gt_chars": cn, "cer": ced / cn if cn else None,
                "word_edit_distance": wed, "gt_words": wn, "wer": wed / wn if wn else None,
                "punctuation": {**prf(tp, fp, fn), "eligible_rows": punct_rows}}
    ok = [r for r in eligible if not _failed(r)]
    return {"primary_failure_aware": agg(eligible, True), "successful_only": agg(ok, False),
            "eligible": len(eligible), "successful": len(ok), "failed": len(eligible) - len(ok),
            "coverage": len(ok) / len(eligible) if eligible else None,
            "excluded_no_ground_truth": no_gt,
            "punctuation_excluded_ambiguous": [r.get("id") for r in eligible if not r.get("punct_eligible", True)]}


# ---- numeric amount grammar (strict) ----
# [Rs|Rs.|PKR][space] INTEGER [.dd] [/-]
#   INTEGER: 0 | [1-9]\d*                        (no grouping)
#          | [1-9]\d{0,2}(,\d{3})+                (international grouping: 2,500  75,450  100,000)
#          | [1-9]\d?(,\d{2})+,\d{3}              (South Asian grouping: 1,50,000  12,34,567)
#   fraction: exactly two digits. Anything else (12,50  1,,250  ,1250  1250,  1.2.3  1 2 5 0  $5  ₹5) -> None.
NUMERIC_RE = re.compile(
    r"(?:(?P<cur>rs\.?|pkr)\s?)?"
    r"(?P<int>0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+|[1-9][0-9]?(?:,[0-9]{2})+,[0-9]{3})"
    r"(?P<frac>\.[0-9]{2})?(?:/-)?", re.I)  # ASCII [0-9] only (\d would admit other Unicode digits)
# Supported currency markers: Rs, Rs., PKR (case-insensitive) or none. Unsupported (value None -> review):
# ₹, INR, $, S$, USD and any other symbol; a foreign currency is never interpreted as PKR.


def numeric_value(text):
    """Decimal value of a strictly formatted numeral, else None (never repairs or infers digits)."""
    if not isinstance(text, str):
        return None
    m = NUMERIC_RE.fullmatch(text.strip())
    if not m:
        return None
    return Decimal(m.group("int").replace(",", "") + (m.group("frac") or ""))


# ---- written amount grammar (conservative) ----
# [rupees|rupee|rs] AMOUNT [and FRACTION paisa|paise] [rupees|rupee] [only]   (at most one 'rupees')
#   AMOUNT = (GROUP SCALE)* [and] [GROUP]   scales strictly decreasing, each at most once:
#            Indian: crore > lakh > thousand (multipliers 1-99);  international: million > thousand (1-999)
#            Indian and international scales are never mixed. 'and' only after 'hundred' or a scale word.
#   GROUP  = [UNIT1-9 hundred [and]] [BELOW100]  (at least one part);  BELOW100 = 1..19 | TENS [UNIT1-9]
#   FRACTION = BELOW100 (1-99). Case-insensitive; '-' between words = space; no commas or other symbols.
UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)}
SCALES = {"crore": (10**7, 4, "indian"), "lakh": (10**5, 3, "indian"), "lac": (10**5, 3, "indian"),
          "lakhs": (10**5, 3, "indian"), "million": (10**6, 3, "intl"), "thousand": (10**3, 2, None)}


def _below100(ws, i):
    if i < len(ws) and ws[i] in UNITS and UNITS[ws[i]] >= 1:
        return UNITS[ws[i]], i + 1
    if i < len(ws) and ws[i] in TENS:
        v, i = TENS[ws[i]], i + 1
        if i < len(ws) and ws[i] in UNITS and 1 <= UNITS[ws[i]] <= 9:
            v, i = v + UNITS[ws[i]], i + 1
        return v, i
    return None, i


def _group(ws, i):
    """GROUP -> (value, next_index, ended_with_hundred) or (None, i, False)."""
    if i + 1 < len(ws) and ws[i] in UNITS and 1 <= UNITS[ws[i]] <= 9 and ws[i + 1] == "hundred":
        v, j = UNITS[ws[i]] * 100, i + 2
        k = j + 1 if j < len(ws) and ws[j] == "and" else j
        b, k2 = _below100(ws, k)
        if b is not None:
            return v + b, k2, False
        return (v, j, True) if k == j else (None, i, False)  # dangling 'and' is invalid
    b, j = _below100(ws, i)
    return (b, j, False) if b is not None else (None, i, False)


def _amount(ws):
    if not ws:
        return None
    total, i, last_rank, system = 0, 0, 99, None
    while i < len(ws):
        if ws[i] == "and":
            if i == 0 or ws[i - 1] not in SCALES:  # 'and' only right after a scale word here
                return None
            i += 1
        g, j, _ = _group(ws, i)
        if g is None:
            return None
        if j < len(ws) and ws[j] in SCALES:
            scale, rank, sys_ = SCALES[ws[j]]
            if rank >= last_rank or (sys_ and system and sys_ != system):
                return None
            system = system or sys_
            limit = 100 if (system == "indian") else 1000
            if g >= limit:
                return None
            total, i, last_rank = total + g * scale, j + 1, rank
        else:
            if j != len(ws):
                return None
            return total + g
    return total if last_rank < 99 else None


def words_value(text):
    """Decimal value of an English written amount, else None. No fuzzy matching, spell correction or
    segmentation: unspaced text such as 'fivethousandonly' returns None."""
    if not isinstance(text, str) or not re.fullmatch(r"[A-Za-z]+(?:[ -]+[A-Za-z]+)*", text.strip()):
        return None
    ws = re.sub(r"-", " ", text.strip().lower()).split()
    if ws and ws[-1] == "only":
        ws = ws[:-1]
    cur = [k for k, w in enumerate(ws) if w in ("rupees", "rupee", "rs")]
    if len(cur) > 1 or (cur and cur[0] not in (0, len(ws) - 1)):
        return None
    if cur:
        ws = ws[1:] if cur[0] == 0 else ws[:-1]
    if "only" in ws or "zero" in ws:
        return None
    frac = Decimal(0)
    if ws and ws[-1] in ("paisa", "paise"):
        k = len(ws) - 1
        p, j = None, None
        for s in range(k - 1, 0, -1):  # the 'and' that introduces the fraction
            if ws[s] == "and":
                p, j = _below100(ws, s + 1)
                break
        if p is None or j != k:
            return None
        frac, ws = Decimal(p) / 100, ws[:s]
    v = _amount(ws)
    return None if v is None else Decimal(v) + frac


def decide(num_val, words_val):
    """Discrepancy decision: review if either value is unavailable, accept if equal, flag otherwise."""
    if num_val is None or words_val is None:
        return "review"
    return "accept" if num_val == words_val else "flag"


LABELS, DECISIONS = ("match", "mismatch"), ("accept", "flag", "review")


def discrepancy_metrics(items):
    """items: dicts with 'label' (verified 'match'|'mismatch'; anything else = unresolved, excluded and counted)
    and 'decision' ('accept'|'flag'|'review'; anything else raises). Positive class = mismatch.
    Primary (conservative): flag OR review counts as positive."""
    bad = [x for x in items if x.get("decision") not in DECISIONS]
    if bad:
        raise ValueError(f"invalid decision(s): {sorted({str(x.get('decision')) for x in bad})}")
    elig = [x for x in items if x.get("label") in LABELS]
    unresolved = [x.get("id") for x in items if x.get("label") not in LABELS]
    cm = {(l, d): sum(1 for x in elig if x["label"] == l and x["decision"] == d) for l in LABELS for d in DECISIONS}
    assert sum(cm.values()) == len(elig)
    n_mis = sum(v for (l, _), v in cm.items() if l == "mismatch")
    n_mat = len(elig) - n_mis
    tp = cm[("mismatch", "flag")] + cm[("mismatch", "review")]
    fp = cm[("match", "flag")] + cm[("match", "review")]
    decided = [x for x in elig if x["decision"] != "review"]
    s = prf(sum(1 for x in decided if x["label"] == "mismatch" and x["decision"] == "flag"),
            sum(1 for x in decided if x["label"] == "match" and x["decision"] == "flag"),
            sum(1 for x in decided if x["label"] == "mismatch" and x["decision"] == "accept"))
    reviews = cm[("match", "review")] + cm[("mismatch", "review")]
    return {"n_items": len(items), "n_eligible": len(elig), "unresolved_excluded": unresolved,
            "confusion": {f"{l}->{d}": v for (l, d), v in cm.items()},
            "primary_flag_or_review_positive": prf(tp, fp, cm[("mismatch", "accept")]),
            "incorrect_acceptance_rate": cm[("mismatch", "accept")] / n_mis if n_mis else None,
            "incorrect_rejection_rate": cm[("match", "flag")] / n_mat if n_mat else None,
            "manual_review_rate": reviews / len(elig) if elig else None,
            "all_review": bool(elig) and reviews == len(elig),
            "secondary_decided_only": {**s, "n_decided": len(decided)}}


def latency_stats(seconds):
    s = sorted(seconds)
    if not s:
        return {"n": 0, "median": None, "p95": None, "total": 0}
    return {"n": len(s), "median": statistics.median(s), "p95": s[math.ceil(0.95 * len(s)) - 1], "total": sum(s)}


if __name__ == "__main__":
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().parent.parent / "tests" / "test_m4_audit.py"), run_name="__main__")
