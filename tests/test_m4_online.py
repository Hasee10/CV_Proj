"""M4-ONLINE regression tests: pending audit fixes, pair validation, benchmark integrity. Temporary fixtures only.
Run: .venv\\Scripts\\python.exe -X utf8 -I tests\\test_m4_online.py [--out artifacts\\M4_ONLINE\\TEST_RESULTS.json]
"""
import ast
import csv
import hashlib
import io
import json
import sys
import tempfile
import time
import traceback
import zipfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from PIL import Image  # noqa: E402

import build_online_benchmarks as bob  # noqa: E402
import custom_sheets as cs  # noqa: E402
import eval_metrics as em  # noqa: E402
import validate_manifest as vm  # noqa: E402

B = ROOT / "data/benchmarks"


def load(name):
    return json.loads((B / name / "manifest.json").read_text(encoding="utf-8"))


# ---- pending audit fix 3: ASCII digits and currencies ----
def test_numeric_ascii_digits_and_currencies():
    for t in ["1٢34", "１２３", "2,5００", "١٢٣٤", "12,5०0", "₹500", "INR 500", "S$500", "$500", "USD 500", "Rs$500", "€500"]:
        assert em.numeric_value(t) is None, t
    assert em.numeric_value("Rs 500") == Decimal("500") and em.numeric_value("PKR 1,250.00") == Decimal("1250.00")


# ---- pending audit fix 2: finite, non-negative, <= 2 decimals ----
def test_human_values_finite_nonnegative_two_decimals():
    for t in ["NaN", "nan", "sNaN", "Infinity", "-Infinity", "inf", "-5", "1.234", "", "abc", "1e3x", " "]:
        assert cs.valid_money(t) is None, t
    for t, v in [("12000", "12000"), ("1250.00", "1250.00"), ("0", "0"), ("7.5", "7.5"), ("1E+3", "1000")]:
        assert cs.valid_money(t) == Decimal(v), t


# ---- pending audit fix 1: duplicate annotation ids ----
def test_duplicate_annotation_ids_not_collapsed():
    with tempfile.TemporaryDirectory() as td:
        saved = cs.ANNOT
        cs.ANNOT = Path(td) / "annotation.csv"
        try:
            with open(cs.ANNOT, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cs.FIELDS)
                w.writeheader()
                for v in ("a", "b"):
                    w.writerow({k: "" for k in cs.FIELDS} | {"sample_id": "W01_A01_num", "writer_id": "W01",
                                                              "item_id": "A01", "field": "num", "verified_text": v})
            assert len(cs.read_annotation_rows()) == 2
            try:
                cs.read_annotations()
                raise AssertionError("duplicates silently collapsed")
            except ValueError:
                pass
            probs = cs.check_annotations(cs.read_annotation_rows())
            assert any("duplicate sample_id" in p for p in probs)
        finally:
            cs.ANNOT = saved


# ---- pair validation and the blank-field duplicate exception ----
def _s(i, split, gv, group, gt="x"):
    return {"id": i, "split": split, "gt_value": gv, "group_id": group, "ground_truth": gt}


def test_validate_pairs_rules():
    ss = [_s("n1", "test", "5", "c1"), _s("w1", "test", "5", "c1"), _s("w2", "test", "6", "c2"), _s("w3", "dev", "5", "c3"),
          _s("n4", "test", None, "c4"), _s("w4", "test", "4", "c4")]
    ok = [{"pair_id": "p1", "num_id": "n1", "words_id": "w1", "split": "test", "label": "match", "construction": "natural_same_cheque"},
          {"pair_id": "p2", "num_id": "n1", "words_id": "w2", "split": "test", "label": "mismatch", "construction": "constructed_cross_cheque"},
          {"pair_id": "p3", "num_id": "n4", "words_id": "w4", "split": "test", "label": "unresolved", "construction": "natural_same_cheque"}]
    assert vm.validate_pairs(ok, ss)["passed"]
    bad = [dict(ok[0], label="mismatch"), dict(ok[1], pair_id="p1"), dict(ok[1], pair_id="p5", words_id="w3"),
           dict(ok[1], pair_id="p6", construction="natural_same_cheque"), dict(ok[0], pair_id="p7", words_id="zz")]
    r = vm.validate_pairs(bad, ss)
    assert not r["passed"] and len(r["errors"]) == 6, r["errors"]  # p5 fails twice: split and label
    assert not vm.validate_pairs([], ss)["passed"]


def test_exact_duplicate_only_cleared_for_reviewed_blank_fields():
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        Image.new("RGB", (40, 20), "white").save(r / "a.png")
        h = hashlib.sha256((r / "a.png").read_bytes()).hexdigest()
        mk = lambda i, sp, gt: {"id": i, "file": "a.png", "sha256": h, "ground_truth": gt, "split": sp, "group_id": i}
        blank = [mk("a", "dev", ""), mk("b", "test", "")]
        assert not vm.validate([dict(x) for x in blank], root=r)["passed"]
        assert vm.validate([dict(x) for x in blank], [{"pair": ["a", "b"], "decision": "blank_field"}], root=r)["passed"]
        text = [mk("a", "dev", "5"), mk("b", "test", "5")]
        assert not vm.validate([dict(x) for x in text], [{"pair": ["a", "b"], "decision": "blank_field"}], root=r)["passed"]


# ---- ground truth independent of the evaluated parsers ----
def test_ground_truth_not_from_evaluated_parser():
    src = (ROOT / "scripts/build_online_benchmarks.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    imported = {n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)} | \
               {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert "eval_metrics" not in imported
    for n in (1, 19, 20, 99, 100, 101, 462, 1005, 3083, 8040, 9999, 12345):
        assert bob.WORDS_TO_INT[bob.verbalize(n)] == n
    agree = 0
    for s in load("syn_cheques")["samples"]:  # cross-check (not the GT source): frozen parser agrees on clean annotations
        if s["category"] == "syn_words" and s["gt_value"] is not None:
            agree += em.words_value(s["ground_truth"]) == Decimal(s["gt_value"])
    assert agree == sum(1 for s in load("syn_cheques")["samples"] if s["category"] == "syn_words" and s["gt_value"])


# ---- benchmark integrity on the real acquired files (read-only) ----
def test_cvl_subset_integrity():
    m = load("cvl_numeric")
    z = zipfile.ZipFile(ROOT / "data/public/cvl/cache/cvl-strings-train.zip")
    assert len(m["samples"]) == 300 and hashlib.md5((ROOT / "data/public/cvl/cache/cvl-strings-train.zip").read_bytes()).hexdigest() == m["archive_md5"]
    for s in m["samples"]:
        assert (ROOT / s["file"]).read_bytes() == z.read(s["source_entry"])          # byte-identical to the original
        assert s["ground_truth"] == s["source_entry"].split("/")[-1].split("-")[0]  # label from filename
    splits = {}
    for s in m["samples"]:
        splits.setdefault(s["writer_id"], set()).add(s["split"])
    assert all(len(v) == 1 for v in splits.values()) and len(splits) == 30
    assert sum(1 for v in splits.values() if "dev" in v) == 9


def test_gnhk_pairs_respect_frozen_page_split():
    sub = json.loads((ROOT / "data/public/gnhk/subset/manifest.json").read_text(encoding="utf-8"))
    pages = {p: v["split"] for p, v in sub["pages"].items()}
    for s in load("gnhk_pairs")["samples"]:
        if s["group_id"] in pages:
            assert pages[s["group_id"]] == s["split"], s["id"]
        if s["also_in_gnhk_subset_as"]:
            twin = next(x for x in sub["samples"] if x["id"] == s["also_in_gnhk_subset_as"])
            assert twin["sha256"] == s["sha256"] and twin["split"] == s["split"]


def test_synthetic_crops_reproducible_and_lineage():
    m = load("syn_cheques")
    for s in m["samples"][:40]:
        raw = (ROOT / s["source_file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == s["source_sha256"]
        buf = io.BytesIO()
        Image.open(io.BytesIO(raw)).convert("RGB").crop(tuple(s["crop_box_xyxy"])).save(buf, "PNG")
        assert Image.open(buf).tobytes() == Image.open(ROOT / s["file"]).convert("RGB").tobytes()
        assert s["genuine_handwriting"] is False


def test_full_validation_passes():
    ms = [ROOT / "data/public/gnhk/subset/manifest.json"] + [B / n / "manifest.json" for n in ("cvl_numeric", "gnhk_pairs", "syn_cheques")]
    ss = [s for p in ms for s in json.loads(p.read_text(encoding="utf-8"))["samples"]]
    review = json.loads((B / "duplicate_review.json").read_text(encoding="utf-8"))
    rep = vm.validate([dict(s) for s in ss], review)
    assert rep["passed"], rep["errors"][:5]
    pr = vm.validate_pairs(json.loads((B / "amount_pairs.json").read_text(encoding="utf-8"))["pairs"], ss)
    assert pr["passed"] and pr["labels"] == {"match": 119, "mismatch": 147, "unresolved": 24}, pr


def test_previous_suite_still_passes():
    import subprocess
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", str(ROOT / "tests/test_m4_audit.py")], capture_output=True, text=True)
    assert r.returncode == 0 and "27/27 passed" in r.stdout, r.stdout[-500:]


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
        Path(out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
