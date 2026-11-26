"""M4-AUDIT regression tests (plain Python, no pytest). All fixtures live in temporary folders;
synthetic sheet renders are software-test fixtures only and never enter data/.
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m4_audit.py [--out artifacts\\M4_AUDIT\\TEST_RESULTS.json]
"""
import csv
import json
import sys
import tempfile
import time
import traceback
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cv2  # noqa: E402
import numpy as np  # noqa: E402

import custom_sheets as cs  # noqa: E402
import eval_metrics as em  # noqa: E402
import stress_corrupt as sc  # noqa: E402
import validate_manifest as vm  # noqa: E402

D = Decimal


# ---------------- 1. numeric parser ----------------
def test_numeric_accepts():
    ok = {"2500": "2500", "2,500": "2500", "100000": "100000", "1,250.00": "1250.00", "75,450.50": "75450.50",
          "Rs. 3,000/-": "3000", "PKR 18,750": "18750", "500": "500", "250.50": "250.50", "Rs.3,000/-": "3000",
          "rs 500": "500", "1,50,000": "150000", "12,34,567": "1234567", "0": "0", " 2,500 ": "2500",
          "260,000": "260000", "8,040.75": "8040.75", "1,005": "1005", "PKR18,750": "18750"}
    for t, v in ok.items():
        assert em.numeric_value(t) == D(v), (t, em.numeric_value(t))


def test_numeric_rejects():
    bad = ["1,,250", ",1250", "1250,", "12,50", "1.2.3", "1 2 5 0", "", "   ", None, "$500", "₹500", "USD 500",
           "Rs. PKR 500", "0500", "1250.5", "125,0000", "1,5,000", "1250-00", "12,500.000", "Rs", "/-", ".50",
           "1,250.", "Rs. 3,000/-/-", "3,000 Rs", "1,23,45", "١٢٣", 1250]
    for t in bad:
        assert em.numeric_value(t) is None, (t, em.numeric_value(t))


def test_numeric_never_repairs_decimal():
    assert em.numeric_value("125000") == D("125000")       # model output for GT 1250.00 stays wrong
    assert em.numeric_value("125000") != D("1250.00")


# ---------------- 2. written-amount parser ----------------
def test_words_accepts():
    ok = {"Five hundred only": "500", "Twelve thousand five hundred only": "12500",
          "One hundred thousand only": "100000", "Rupees three thousand only": "3000",
          "One lakh fifty thousand only": "150000",
          "Seventy five thousand four hundred fifty and fifty paisa only": "75450.50",
          "Two hundred fifty and fifty paisa only": "250.50", "TWELVE THOUSAND FIVE HUNDRED ONLY": "12500",
          "twenty-five": "25", "One thousand and five": "1005", "two hundred and fifty": "250",
          "Five thousand rupees only": "5000", "one crore two lakh three thousand": "10203000",
          "two million five hundred thousand": "2500000", "Rupee one only": "1",
          "nine thousand nine hundred ninety nine": "9999", "eight thousand forty and seventy five paisa": "8040.75"}
    for t, v in ok.items():
        assert em.words_value(t) == D(v), (t, em.words_value(t))


def test_words_rejects():
    bad = ["five five", "and", "hundred hundred", "thousand thousand", "twenty thirty", "five twenty", "only",
           "rupees", "rupees rupees five", "fifty thousand twelve thousand", "one thousand one lakh",
           "one million one lakh", "hundred", "one hundred and", "and fifty paisa", "five and", "fifty paisa",
           "five hundred and one hundred paisa", "fivethousandonly", "Five thousand, only", "zero", "Five thousand.",
           "one lakh two hundred thousand", "five only rupees", "only five", "eleven hundred", "five rupees five",
           "", None, "five thousand and", "and five thousand", "one hundred one hundred", "twenty twenty",
           "five thousand five thousand", "one and two", "five hundred and paisa", "seventy five paise"]
    for t in bad:
        assert em.words_value(t) is None, (t, em.words_value(t))


def test_all_21_designed_pairs():
    assert len(cs.ITEMS) == 21 and sum(i[5] == "match" for i in cs.ITEMS) == 15
    assert sum(i[5] == "mismatch" for i in cs.ITEMS) == 6
    for s in "ABC":
        assert sum(i[0][0] == s for i in cs.ITEMS) == 7
    for it in cs.ITEMS:
        nv, wv = em.numeric_value(it[1]), em.words_value(it[2])
        assert nv == D(it[3]) and wv == D(it[4]), it
        assert (it[5] == "match") == (nv == wv), it
        assert em.decide(nv, wv) == ("accept" if it[5] == "match" else "flag"), it


# ---------------- 4. failure-aware metrics ----------------
def test_failure_aware_ignores_stale_prediction():
    t = em.text_metrics([{"id": "a", "gt": "abc", "pred": "abc", "error": "inference failed"}])
    p = t["primary_failure_aware"]
    assert p["exact"] == 0 and p["cer"] == 1.0 and t["failed"] == 1 and t["coverage"] == 0.0
    assert t["successful_only"]["n"] == 0


def test_missing_none_empty_predictions():
    rows = [{"id": "m", "gt": "ab"}, {"id": "n", "gt": "ab", "pred": None, "error": None},
            {"id": "e", "gt": "ab", "pred": "", "error": None}, {"id": "ok", "gt": "ab", "pred": "ab"},
            {"id": "h", "gt": "ab", "pred": "ab", "error": "sha256 mismatch against manifest"}]
    t = em.text_metrics(rows)
    assert t["eligible"] == 5 and t["failed"] == 3 and t["successful"] == 2
    assert t["primary_failure_aware"]["char_edit_distance"] == 8 and t["primary_failure_aware"]["exact"] == 1
    assert t["successful_only"]["char_edit_distance"] == 2 and t["successful_only"]["exact"] == 1


def test_empty_ground_truth_policy():
    t = em.text_metrics([{"id": "x", "gt": "", "pred": "a"}, {"id": "y", "pred": "a"}, {"id": "z", "gt": "a", "pred": "a"}])
    assert t["eligible"] == 1 and sorted(t["excluded_no_ground_truth"]) == ["x", "y"]


def test_punctuation_alignment_and_exclusion():
    assert em.punct_counts("125000", "1250.00") == (0, 0, 1)
    assert em.punct_counts("75,450.50", "75,450.50") == (2, 0, 0)
    assert em.punct_counts("1250,00", "1250.00") == (0, 1, 1)
    assert em.punct_counts("1,2500", "12,500") == (0, 1, 1)
    t = em.text_metrics([{"id": "H04", "gt": "1250-00", "pred": "125000", "punct_eligible": False},
                         {"id": "H05", "gt": "75,450.50", "pred": "18050"}])
    pu = t["primary_failure_aware"]["punctuation"]
    assert pu["eligible_rows"] == 1 and pu["fn"] == 2 and t["punctuation_excluded_ambiguous"] == ["H04"]


def test_discrepancy_invalid_decision_raises():
    try:
        em.discrepancy_metrics([{"label": "match", "decision": "maybe"}])
    except ValueError:
        return
    raise AssertionError("invalid decision accepted")


def test_discrepancy_labels_totals_and_review():
    items = [{"id": 1, "label": "mismatch", "decision": "flag"}, {"id": 2, "label": "mismatch", "decision": "accept"},
             {"id": 3, "label": "match", "decision": "accept"}, {"id": 4, "label": "match", "decision": "review"},
             {"id": 5, "label": "unresolved", "decision": "review"}, {"id": 6, "label": None, "decision": "accept"},
             {"id": 7, "label": "Match", "decision": "accept"}]
    m = em.discrepancy_metrics(items)
    assert m["n_eligible"] == 4 and sorted(m["unresolved_excluded"]) == [5, 6, 7]
    assert sum(m["confusion"].values()) == 4
    assert m["primary_flag_or_review_positive"]["tp"] == 1 and m["incorrect_acceptance_rate"] == 0.5
    assert m["manual_review_rate"] == 0.25 and m["secondary_decided_only"]["n_decided"] == 3 and not m["all_review"]
    allr = em.discrepancy_metrics([{"label": "match", "decision": "review"}, {"label": "mismatch", "decision": "review"}])
    assert allr["all_review"] and allr["primary_flag_or_review_positive"]["recall"] == 1.0
    assert allr["manual_review_rate"] == 1.0 and allr["secondary_decided_only"]["n_decided"] == 0


def test_latency_stats():
    assert em.latency_stats([1, 2, 3, 4, 100])["p95"] == 100 and em.latency_stats([])["median"] is None


# ---------------- 5. custom sheets ----------------
class TmpCustom:
    """Point custom_sheets at an isolated temporary tree."""
    def __enter__(self):
        self.td = tempfile.TemporaryDirectory()
        r = Path(self.td.name)
        self.saved = {k: getattr(cs, k) for k in ("ROOT", "TPL", "RAW", "CROPS", "ANNOT", "MANIFEST")}
        cs.ROOT, cs.TPL, cs.RAW, cs.CROPS = r, r / "tpl", r / "raw", r / "crops"
        cs.ANNOT, cs.MANIFEST = r / "annotation.csv", r / "manifest.json"
        for d in (cs.TPL, cs.RAW):
            d.mkdir()
        (cs.TPL / "layout.json").write_text(json.dumps(cs.layout()), encoding="utf-8")
        return r

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(cs, k, v)
        self.td.cleanup()


def photo(sheet, variant=0):
    lay = cs.layout()
    page = np.array(cs.render(sheet, lay).convert("RGB"))[:, :, ::-1]
    big = cv2.copyMakeBorder(page, 200, 200, 200, 200, cv2.BORDER_CONSTANT, value=(200, 200, 200))
    hh, ww = big.shape[:2]
    j = 20 * variant
    src = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])
    dst = np.float32([[60 + j, 30], [ww - 30, 90 + j], [ww - 90, hh - 20], [20, hh - 70 - j]])
    out = cv2.warpPerspective(big, cv2.getPerspectiveTransform(src, dst), (ww, hh), borderValue=(90, 90, 90))
    return cv2.resize(out, None, fx=0.7, fy=0.7, interpolation=cv2.INTER_AREA)


def put(name, sheet, variant=0):
    assert cv2.imwrite(str(cs.RAW / name), photo(sheet, variant))


def mark_all(status="verified"):
    rows = list(cs.read_annotations().values())
    for r in rows:
        r.update({"verification_status": status, "deviation": "no", "verifier": "T"})
    cs.write_annotations(rows)
    return rows


def test_rectify_no_markers_and_wrong_sheet():
    lay = cs.layout()
    blank = np.full((800, 600, 3), 255, np.uint8)
    assert cs.rectify(blank, "A", lay) == (None, [])
    assert cs.rectify(photo("A"), "B", lay)[0] is None
    assert cs.rectify(photo("A"), "A", lay)[0] is not None


def test_extract_names_duplicates_unreadable():
    with TmpCustom():
        put("W01_A.jpg", "A")
        put("W01_A.jpeg", "A")
        put("bad name.jpg", "A")
        (cs.RAW / "W01_B.jpg").write_bytes(b"not an image")
        put("W02_C.jpg", "A")                    # wrong sheet content for the name
        assert cs.extract() == 1
        rows = cs.read_annotations()
        assert not any(k.startswith("W01_A") for k in rows) and not any(k.startswith("W02_C") for k in rows)
        assert not any(k.startswith("W01_B") for k in rows)


def test_extract_pilot_only_and_refuses_frozen():
    with TmpCustom():
        put("W01_A.jpg", "A")
        put("W02_A.jpg", "A", 1)
        assert cs.extract("W01_A") == 0
        rows = cs.read_annotations()
        assert len(rows) == 14 and all(k.startswith("W01_A") for k in rows)
        assert all(r["verification_status"] == "pending" for r in rows.values())
        cs.MANIFEST.write_text("{}", encoding="utf-8")
        assert cs.extract("W02_A") == 2 and len(cs.read_annotations()) == 14


def test_annotation_preserved_or_flagged():
    with TmpCustom():
        put("W01_A.jpg", "A")
        cs.extract("W01_A")
        mark_all()
        assert cs.extract("W01_A") == 0              # identical photo: verification kept
        assert all(r["verification_status"] == "verified" and not r["reverify_reason"]
                   for r in cs.read_annotations().values())
        put("W01_A.jpg", "A", 2)                      # replaced photo: verification must not carry over
        assert cs.extract("W01_A") == 0
        rows = cs.read_annotations().values()
        assert all(r["verification_status"] == "pending" and r["reverify_reason"] and "prev:verified" in r["history"]
                   for r in rows)
        assert len(list((cs.ANNOT.parent / "annotation_backups").iterdir())) >= 2


def test_finalize_incomplete_reports_missing():
    with TmpCustom():
        put("W01_A.jpg", "A")
        cs.extract()
        mark_all()
        probs = cs.check_annotations(list(cs.read_annotations().values()))
        assert any("need >= 4 writers" in p for p in probs) and any("missing W01_B01_num" in p for p in probs)
        assert cs.finalize() == 1 and not cs.MANIFEST.exists()


def test_finalize_rejects_duplicates_and_pending():
    with TmpCustom():
        put("W01_A.jpg", "A")
        cs.extract()
        rows = list(cs.read_annotations().values())
        dup = dict(rows[0], sample_id="W01_A01_num_copy")
        probs = cs.check_annotations(rows + [dup, dict(rows[1])])
        assert any("duplicate writer/item/field" in p for p in probs)
        assert any("duplicate sample_id" in p for p in probs)
        assert any("verification_status must be" in p for p in probs)


def test_finalize_complete_independent_values_and_split():
    with TmpCustom() as r:
        for wi, w in enumerate(["W01", "W02", "W03", "W04", "W05"]):
            for s in "ABC":
                put(f"{w}_{s}.jpg", s, wi % 3)
        assert cs.extract() == 0
        rows = mark_all()
        for row in rows:
            if row["sample_id"] == "W03_A01_num":     # writer wrote 5,000 instead of 500
                row.update(deviation="yes", verified_text="5,000", verified_value="5000")
            if row["sample_id"] == "W04_B02_words":   # illegible words field
                row.update(verification_status="unresolved", deviation="", unresolved_reason="illegible")
        cs.write_annotations(rows)
        real = (cs.numeric_value, cs.words_value)
        cs.numeric_value = cs.words_value = lambda *_: (_ for _ in ()).throw(AssertionError("parser used for GT"))
        try:
            assert cs.finalize() == 0
        finally:
            cs.numeric_value, cs.words_value = real
        m = json.loads(cs.MANIFEST.read_text(encoding="utf-8"))
        assert len(m["samples"]) == 210 and "W01" in m["dev_writers"]
        assert len(m["dev_writers"]) == 2 and len(m["test_writers"]) == 3
        by = {s["id"]: s for s in m["samples"]}
        assert by["W03_A01_num"]["gt_value"] == "5000" and by["W03_A01_num"]["pair_label"] == "mismatch"
        assert by["W04_B02_words"]["gt_value"] is None and by["W04_B02_num"]["pair_label"] == "unresolved"
        assert by["W02_A04_num"]["pair_label"] == "mismatch" and by["W02_A01_words"]["pair_label"] == "match"
        # blank fixture boxes look alike -> cross-split near-duplicate candidates that MUST be reviewed
        rep = vm.validate([dict(s) for s in m["samples"]], root=r)
        assert not rep["passed"] and rep["near_duplicates_unresolved"]
        assert all(e.startswith("near-duplicate candidate") for e in rep["errors"]), rep["errors"][:3]
        reviewed = [{"pair": u["pair"], "decision": "not_duplicate", "reviewer": "T"} for u in rep["near_duplicates_unresolved"]]
        rep2 = vm.validate([dict(s) for s in m["samples"]], reviewed, root=r)
        assert rep2["passed"], rep2["errors"][:5]
        assert cs.finalize() == 2                       # frozen manifest is never overwritten


# ---------------- 7. manifest validation ----------------
def _img(path, seed, tweak=False):
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 255, (40, 120, 3)).astype(np.uint8)
    if tweak:
        a[0, 0, 0] ^= 1
    assert cv2.imwrite(str(path), a)
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _s(i, split, f, h, **kw):
    return {"id": i, "file": f, "sha256": h, "ground_truth": "x", "split": split, "group_id": i, **kw}


def test_validator_core_failures():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        h = _img(r / "a.png", 1)
        assert not vm.validate([], root=r)["passed"]
        assert not vm.validate([_s("a", "dev", "a.png", h), _s("a", "dev", "a.png", h)], root=r)["passed"]
        assert not vm.validate([{"id": "a", "file": "a.png", "sha256": h, "split": "dev"}], root=r)["passed"]
        assert not vm.validate([_s("a", "dev", "a.png", "0" * 64)], root=r)["passed"]
        assert not vm.validate([_s("a", "dev", "missing.png", h)], root=r)["passed"]
        assert vm.validate([_s("a", "dev", "a.png", h)], root=r)["passed"]


def test_validator_near_duplicates_need_review():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        ha, hb = _img(r / "a.png", 7), _img(r / "b.png", 7, tweak=True)
        ss = [_s("a", "dev", "a.png", ha), _s("b", "test", "b.png", hb)]
        rep = vm.validate([dict(x) for x in ss], root=r)
        assert not rep["passed"] and rep["near_duplicates_unresolved"]
        ok = vm.validate([dict(x) for x in ss], [{"pair": ["b", "a"], "decision": "not_duplicate", "reviewer": "T"}], root=r)
        assert ok["passed"], ok["errors"]
        dup = vm.validate([dict(x) for x in ss], [{"pair": ["a", "b"], "decision": "duplicate"}], root=r)
        assert not dup["passed"]
        same = vm.validate([_s("a", "dev", "a.png", ha), _s("c", "test", "a.png", ha)], root=r)
        assert not same["passed"] and same["cross_split_exact_duplicates"]


def test_validator_pairs_lineage_sources():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        ha, hb, hs = _img(r / "a.png", 1), _img(r / "b.png", 2), _img(r / "src.png", 3)
        pair = [_s("a", "dev", "a.png", ha, pair_id="P"), _s("b", "test", "b.png", hb, pair_id="P")]
        assert not vm.validate(pair, root=r)["passed"]
        orphan = [_s("v", "dev", "a.png", ha, parent_id="nope")]
        assert not vm.validate(orphan, root=r)["passed"]
        wrong_parent_split = [_s("p", "dev", "a.png", ha), _s("v", "test", "b.png", hb, parent_id="p")]
        assert not vm.validate(wrong_parent_split, root=r)["passed"]
        src_ok = [_s("a", "dev", "a.png", ha, source_file="src.png", source_sha256=hs)]
        assert vm.validate(src_ok, root=r)["passed"]
        src_bad = [_s("a", "dev", "a.png", ha, source_file="src.png", source_sha256="0" * 64)]
        assert not vm.validate(src_bad, root=r)["passed"]


def test_gnhk_subset_integrity_unchanged():
    m = json.loads((ROOT / "data/public/gnhk/subset/manifest.json").read_text(encoding="utf-8"))
    import hashlib
    assert hashlib.sha256((ROOT / "data/public/gnhk/subset/manifest.json").read_bytes()).hexdigest() == \
        "13450762dd5508154fe05878554d4867d7df94e9a30a614f2b80385371c0af56"
    rep = vm.validate(m["samples"])
    assert rep["passed"] and rep["per_split"] == {"dev": 80, "test": 160, "exploratory": 0}
    assert rep["cross_split_near_duplicate_candidates"] == []


# ---------------- 9. stress safeguards ----------------
def test_stress_generation_safeguards():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        h = _img(r / "p.png", 5)
        man = r / "m.json"
        man.write_text(json.dumps({"samples": [_s("p", "dev", "p.png", h, pair_id="W09_A01", category="custom_num",
                                                  writer_id="W09")]}), encoding="utf-8")
        rows, probs = sc.generate(man, "dev", r / "out", root=r)
        assert not probs and len(rows) == 15
        assert all(x["pair_id"] == "W09_A01" and x["split"] == "dev" and x["parent_id"] == "p"
                   and x["parent_sha256"] == h and x["category"] == "custom_num" for x in rows)
        parent = json.loads(man.read_text())["samples"]
        rep = vm.validate([dict(x) for x in parent + rows], root=r)
        assert not [e for e in rep["errors"] if "parent" in e or "spans" in e]
        _, p2 = sc.generate(man, "dev", r / "out", root=r)
        assert p2 and "refusing" in p2[0]
        _img(r / "p.png", 6)                           # tampered source
        _, p3 = sc.generate(man, "dev", r / "out2", root=r)
        assert p3 and "sha256 mismatch" in p3[0] and not (r / "out2").exists()


# ---------------- existing self-tests and inference guard ----------------
def test_existing_selftests():
    cs.selftest()
    sc.selftest()


def test_inference_input_hash_guard():
    import smoke_inference as si
    f = ROOT / "data/handwritten_examples/crops/H01.png"
    assert si.readable(f, "deadbeef") == "sha256 mismatch against manifest"
    assert si.readable(f, si.sha256(f)) is None


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out and Path(out).exists():
        print(f"ERROR: {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    results = []
    for name, fn in [(k, v) for k, v in globals().items() if k.startswith("test_") and callable(v)]:
        t0 = time.perf_counter()
        try:
            fn()
            results.append({"test": name, "status": "passed", "seconds": round(time.perf_counter() - t0, 3)})
        except Exception as e:
            results.append({"test": name, "status": "failed", "seconds": round(time.perf_counter() - t0, 3),
                            "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]})
    summary = {"total": len(results), "passed": sum(r["status"] == "passed" for r in results),
               "failed": sum(r["status"] == "failed" for r in results), "results": results}
    for r in results:
        print(f"{r['status']:6} {r['test']} ({r['seconds']}s) {r.get('error', '')}")
    print(f"{summary['passed']}/{summary['total']} passed")
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
