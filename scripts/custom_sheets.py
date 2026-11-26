"""Custom handwritten amount dataset: printable sheets, crop extraction, verified manifest + split.

  make      -> data/custom/template/{amount_list.csv, layout.json, collection_sheets.pdf, sheet_*.png}
  extract [--only W01_A] -> reads data/custom/raw/{WRITER}_{SHEET}.jpg (pilot: one photo), rectifies each photo with its 4 ArUco markers,
               crops every answer box (template-registered crop, NOT a learned detector) and writes
               data/custom/crops/*.png + data/custom/annotation.csv (merge: verified rows are kept only if
               photo and crop hashes are unchanged; otherwise flagged for re-verification)
  finalize  -> checks completeness (>=4 writers, W01, sheets A-C, 21 pairs x 2 fields, statuses, hashes),
               builds data/custom/manifest.json (never overwritten) with human-verified values (not the
               parser) and a writer-disjoint dev/test split (seeded); W01 = the M3-B writer, always dev
Self-test: .venv\\Scripts\\python.exe -X utf8 -I scripts\\custom_sheets.py selftest
"""
import csv
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from eval_metrics import numeric_value, words_value  # noqa: E402

TPL, RAW, CROPS = ROOT / "data/custom/template", ROOT / "data/custom/raw", ROOT / "data/custom/crops"
ANNOT, MANIFEST = ROOT / "data/custom/annotation.csv", ROOT / "data/custom/manifest.json"
W, H, DPI = 1654, 2339, 200                        # A4 at 200 dpi
MK, MARGIN = 110, 50                               # ArUco marker size / margin (px)
ROW_Y0, ROW_H, NUM_W, BOX_H = 255, 262, 620, 100
X0, X1 = 120, W - 120
SEED, DEV_FRACTION, M3B_WRITER = 20261126, 0.3, "W01"
ARUCO = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# item, numeric prompt, words prompt, numeric value, words value, design label, features
ITEMS = [
    ("A01", "500", "Five hundred only", "500", "500", "match", "small"),
    ("A02", "2,500", "Two thousand five hundred only", "2500", "2500", "match", "comma"),
    ("A03", "12,500", "Twelve thousand five hundred only", "12500", "12500", "match", "comma"),
    ("A04", "50,000", "Five thousand only", "50000", "5000", "mismatch", "comma;repeated_zeros;magnitude"),
    ("A05", "100000", "One hundred thousand only", "100000", "100000", "match", "no_separator;repeated_zeros"),
    ("A06", "1,250.00", "One thousand two hundred fifty only", "1250.00", "1250", "match", "comma;decimal"),
    ("A07", "7,200", "Seven thousand only", "7200", "7000", "mismatch", "comma;omitted_hundreds"),
    ("B01", "Rs. 3,000/-", "Rupees three thousand only", "3000", "3000", "match", "currency;comma;suffix"),
    ("B02", "75,450.50", "Seventy five thousand four hundred fifty and fifty paisa only", "75450.50", "75450.50", "match", "comma;decimal;long_words"),
    ("B03", "9,999", "Nine thousand nine hundred ninety nine only", "9999", "9999", "match", "comma;repeated_digits"),
    ("B04", "6,500", "Five thousand six hundred only", "6500", "5600", "mismatch", "comma;transposed"),
    ("B05", "PKR 18,750", "Eighteen thousand seven hundred fifty only", "18750", "18750", "match", "currency;comma"),
    ("B06", "1,005", "One thousand five only", "1005", "1005", "match", "comma;inner_zeros"),
    ("B07", "15,000", "One lakh fifty thousand only", "15000", "150000", "mismatch", "comma;lakh;magnitude"),
    ("C01", "40,000", "Forty thousand only", "40000", "40000", "match", "comma;repeated_zeros"),
    ("C02", "260,000", "Two hundred sixty thousand only", "260000", "260000", "match", "comma;repeated_zeros"),
    ("C03", "8,040.75", "Eight thousand forty and seventy five paisa only", "8040.75", "8040.75", "match", "comma;decimal;inner_zero"),
    ("C04", "Rs. 2,100/-", "Rupees one thousand two hundred only", "2100", "1200", "mismatch", "currency;suffix;transposed"),
    ("C05", "30,000", "Thirty thousand only", "30000", "30000", "match", "comma;repeated_zeros"),
    ("C06", "45,600", "Forty five thousand only", "45600", "45000", "mismatch", "comma;omitted_hundreds"),
    ("C07", "250.50", "Two hundred fifty and fifty paisa only", "250.50", "250.50", "match", "decimal"),
]
SHEETS = sorted({i[0][0] for i in ITEMS})


def font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


def layout():
    marker_ids = {s: list(range(4 * k, 4 * k + 4)) for k, s in enumerate(SHEETS)}  # TL, TR, BR, BL
    corners = [(MARGIN, MARGIN), (W - MARGIN - MK, MARGIN), (W - MARGIN - MK, H - MARGIN - MK), (MARGIN, H - MARGIN - MK)]
    boxes = {}
    for it in ITEMS:
        r = int(it[0][1:]) - 1
        y = ROW_Y0 + r * ROW_H + 40
        boxes[it[0]] = {"num": [X0, y, X0 + NUM_W, y + BOX_H], "words": [X0, y + BOX_H + 12, X1, y + 2 * BOX_H + 12]}
    return {"page_px": [W, H], "dpi": DPI, "marker_px": MK, "marker_corners_tl": corners, "marker_ids": marker_ids,
            "boxes": boxes, "crop_inset_px": 8}


def render(sheet, lay):
    im = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(im)
    for mid, (x, y) in zip(lay["marker_ids"][sheet], lay["marker_corners_tl"]):
        im.paste(Image.fromarray(cv2.aruco.generateImageMarker(ARUCO, mid, MK)), (x, y))
    d.text((MARGIN + MK + 30, 60), f"ChequeVerify handwriting collection - SHEET {sheet}", font=font(40), fill=0)
    for k, line in enumerate(["FICTIONAL PRACTICE SHEET - NOT A CHEQUE. No names, signatures, account or ID numbers.",
                              "Copy each printed amount exactly, in your normal handwriting.",
                              "Number in the short box, words in the long box. Use a dark pen; stay inside the boxes.",
                              "If you make a mistake, leave it: do not cross out or rewrite."]):
        d.text((MARGIN + MK + 30, 112 + 30 * k), line, font=font(22), fill=0)
    for it in ITEMS:
        if it[0][0] != sheet:
            continue
        b = lay["boxes"][it[0]]
        d.text((X0, b["num"][1] - 36), f"{it[0]}   Number: {it[1]}      Words: {it[2]}", font=font(26), fill=0)
        for k in ("num", "words"):
            d.rectangle(b[k], outline=0, width=3)
    return im


def make():
    TPL.mkdir(parents=True, exist_ok=True)
    for it in ITEMS:  # design self-consistency: declared values equal the frozen parsers
        assert numeric_value(it[1]) == Decimal(it[3]), it
        assert words_value(it[2]) == Decimal(it[4]), it
        assert (it[5] == "match") == (Decimal(it[3]) == Decimal(it[4])), it
    lay = layout()
    (TPL / "layout.json").write_text(json.dumps(lay, indent=2), encoding="utf-8")
    with open(TPL / "amount_list.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "sheet", "numeric_prompt", "words_prompt", "numeric_value", "words_value", "pair_label", "features"])
        w.writerows([[i[0], i[0][0], *i[1:]] for i in ITEMS])
    pages = [render(s, lay) for s in SHEETS]
    for s, p in zip(SHEETS, pages):
        p.save(TPL / f"sheet_{s}.png")
    pages[0].save(TPL / "collection_sheets.pdf", save_all=True, append_images=pages[1:], resolution=DPI)
    print(f"{len(ITEMS)} items on {len(SHEETS)} sheets -> {TPL}")


def rectify(img_bgr, sheet, lay):
    """Homography from the 4 detected marker centres to template coordinates.
    Returns (rectified, seen_ids) or (None, seen_ids) when any expected marker is missing (incl. none found)."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = cv2.aruco.ArucoDetector(ARUCO, cv2.aruco.DetectorParameters()).detectMarkers(gray)
    if ids is None or len(ids) == 0:
        return None, []
    found = {int(i): c.reshape(4, 2).mean(0) for i, c in zip(np.asarray(ids).flatten(), corners)}
    want = lay["marker_ids"][sheet]
    if not all(m in found for m in want):
        return None, sorted(found)
    src = np.float32([found[m] for m in want])
    dst = np.float32([(x + MK / 2, y + MK / 2) for x, y in lay["marker_corners_tl"]])
    Hm = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img_bgr, Hm, (W, H), flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255)), sorted(found)


FIELDS = ["sample_id", "writer_id", "sheet", "item_id", "field", "source_photo", "source_sha256", "crop_file",
          "crop_sha256", "prompt_text", "prompt_value", "verification_status", "deviation", "verified_text",
          "verified_value", "ambiguity_note", "unresolved_reason", "verifier", "reverify_reason", "history"]
HUMAN = ["verification_status", "deviation", "verified_text", "verified_value", "ambiguity_note",
         "unresolved_reason", "verifier"]
NAME_RE = re.compile(r"W\d{2}_[ABC]")


def sha_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_annotation_rows():
    if not ANNOT.exists():
        return []
    with open(ANNOT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_annotations():
    """Dict by sample_id; raises on duplicate ids instead of silently keeping the last row."""
    rows = read_annotation_rows()
    ids = [r["sample_id"] for r in rows]
    dups = sorted({i for i in ids if ids.count(i) > 1})
    if dups:
        raise ValueError(f"duplicate sample_id rows in {ANNOT.name}: {dups[:10]}")
    return {r["sample_id"]: r for r in rows}


def valid_money(text):
    """Human-entered value: finite Decimal, >= 0, at most 2 decimal places; else None."""
    try:
        v = Decimal(text.strip())
    except (InvalidOperation, AttributeError):
        return None
    return v if v.is_finite() and v >= 0 and v.as_tuple().exponent >= -2 else None


def write_annotations(rows):
    """Atomic write; the previous file is copied to annotation_backups/ first."""
    if ANNOT.exists():
        bak = ANNOT.parent / "annotation_backups"
        bak.mkdir(exist_ok=True)
        shutil.copy2(ANNOT, bak / f"annotation_{time.strftime('%Y%m%dT%H%M%S')}_{len(list(bak.iterdir()))}.csv")
    tmp = ANNOT.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["sample_id"]))
    os.replace(tmp, ANNOT)


def extract(only=None):
    """Extract crops from data/custom/raw. `only` (e.g. 'W01_A') = pilot for one photo; other rows are kept.
    Existing human verification is preserved only when the source photo AND crop hashes are unchanged."""
    if MANIFEST.exists():
        print(f"ERROR: {MANIFEST} exists (frozen); refusing to re-extract", file=sys.stderr)
        return 2
    lay = json.loads((TPL / "layout.json").read_text(encoding="utf-8"))
    ins, problems = lay["crop_inset_px"], []
    files = [p for p in sorted(RAW.iterdir()) if p.is_file()] if RAW.exists() else []
    by_stem = {}
    for p in files:
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png") or not NAME_RE.fullmatch(p.stem):
            problems.append(f"{p.name}: name must be W<nn>_<A|B|C>.jpg (e.g. W01_A.jpg)")
            continue
        by_stem.setdefault(p.stem, []).append(p)
    for stem, ps in by_stem.items():
        if len(ps) > 1:
            problems.append(f"{stem}: duplicate photos {[p.name for p in ps]}; keep exactly one")
    todo = [ps[0] for stem, ps in sorted(by_stem.items()) if len(ps) == 1 and (only is None or stem == only)]
    if only and not todo:
        problems.append(f"{only}: no single valid photo found")
    if not todo:
        print(f"ERROR: nothing to extract; problems: {problems}", file=sys.stderr)
        return 1
    old, new = read_annotations(), {}
    CROPS.mkdir(parents=True, exist_ok=True)
    for photo in todo:
        writer, sheet = photo.stem.split("_")
        try:  # phones store rotation in EXIF; apply it so markers are found in displayed orientation
            img = cv2.cvtColor(np.array(ImageOps.exif_transpose(Image.open(photo)).convert("RGB")), cv2.COLOR_RGB2BGR)
        except Exception as e:
            problems.append(f"{photo.name}: unreadable ({type(e).__name__})")
            continue
        rect, seen = rectify(img, sheet, lay)
        if rect is None:
            problems.append(f"{photo.name}: markers {lay['marker_ids'][sheet]} not all found (saw {seen}); "
                            "wrong sheet, marker cut off, or retake")
            continue
        src_sha, rows = sha_file(photo), []
        for it in ITEMS:
            if it[0][0] != sheet:
                continue
            for field, text, value in (("num", it[1], it[3]), ("words", it[2], it[4])):
                x0, y0, x1, y1 = lay["boxes"][it[0]][field]
                x0, y0, x1, y1 = x0 + ins, y0 + ins, x1 - ins, y1 - ins
                sid = f"{writer}_{it[0]}_{field}"
                out = CROPS / f"{sid}.png"
                if not (0 <= x0 < x1 <= W and 0 <= y0 < y1 <= H):
                    problems.append(f"{sid}: invalid crop geometry {(x0, y0, x1, y1)}")
                    rows = None
                    break
                if not cv2.imwrite(str(out), rect[y0:y1, x0:x1]):
                    problems.append(f"{sid}: failed to write {out}")
                    rows = None
                    break
                rows.append({"sample_id": sid, "writer_id": writer, "sheet": sheet, "item_id": it[0],
                             "field": field, "source_photo": photo.name, "source_sha256": src_sha,
                             "crop_file": out.relative_to(ROOT).as_posix(), "crop_sha256": sha_file(out),
                             "prompt_text": text, "prompt_value": value, **{k: "" for k in HUMAN},
                             "verification_status": "pending", "reverify_reason": "", "history": ""})
            if rows is None:
                break
        for r in rows or []:
            prev = old.get(r["sample_id"])
            if prev and prev.get("source_sha256") == r["source_sha256"] and prev.get("crop_sha256") == r["crop_sha256"]:
                r.update({k: prev.get(k, "") for k in HUMAN + ["reverify_reason", "history"]})
            elif prev and prev.get("verification_status", "pending") != "pending":
                r["reverify_reason"] = "source photo or crop changed since verification"
                r["history"] = (prev.get("history", "") + f" | prev:{prev.get('verification_status')}:"
                                f"{prev.get('verified_text')}:{prev.get('verified_value')}:{prev.get('verifier')}").strip(" |")
            new[r["sample_id"]] = r
    merged = {**old, **new}
    write_annotations(list(merged.values()))
    flagged = sum(1 for r in new.values() if r["reverify_reason"])
    print(f"extracted {len(new)} crops from {len(todo)} photo(s); annotation rows {len(merged)}; "
          f"re-verify {flagged}; problems: {problems or 'none'}")
    return 0 if not problems else 1


def check_annotations(rows):
    """Return a list of problems that block formal finalisation (empty list = complete)."""
    problems, by_wif = [], {}
    ids = [r["sample_id"] for r in rows]
    problems += [f"duplicate sample_id {s}" for s in sorted({s for s in ids if ids.count(s) > 1})]
    for r in rows:
        k = (r["writer_id"], r["item_id"], r["field"])
        if k in by_wif:
            problems.append(f"duplicate writer/item/field {k}")
        by_wif[k] = r
    writers = sorted({r["writer_id"] for r in rows})
    if len(writers) < 4:
        problems.append(f"need >= 4 writers, have {len(writers)}: {writers}")
    if M3B_WRITER not in writers:
        problems.append(f"{M3B_WRITER} (M3-B writer) missing")
    for wr in writers:
        for it in ITEMS:
            for field in ("num", "words"):
                if (wr, it[0], field) not in by_wif:
                    problems.append(f"missing {wr}_{it[0]}_{field} (sheet {it[0][0]})")
    for r in rows:
        sid, st, dev = r["sample_id"], r.get("verification_status", ""), r.get("deviation", "")
        if r.get("reverify_reason"):
            problems.append(f"{sid}: re-verification required ({r['reverify_reason']})")
        if st not in ("verified", "unresolved"):
            problems.append(f"{sid}: verification_status must be verified or unresolved, is '{st}'")
        if not r.get("verifier", "").strip():
            problems.append(f"{sid}: verifier missing")
        if st == "verified":
            if dev not in ("no", "yes"):
                problems.append(f"{sid}: deviation must be no or yes")
            elif dev == "no" and r.get("verified_text", "").strip() not in ("", r["prompt_text"]):
                problems.append(f"{sid}: verified_text differs from prompt but deviation=no")
            elif dev == "yes":
                if valid_money(r.get("verified_value", "")) is None or not r.get("verified_text", "").strip():
                    problems.append(f"{sid}: deviation=yes needs verified_text and a finite, non-negative "
                                    "verified_value with <= 2 decimals (or mark it unresolved with a reason)")
        if st == "unresolved" and not r.get("unresolved_reason", "").strip():
            problems.append(f"{sid}: unresolved needs unresolved_reason")
        for path_key, sha_key, base in (("source_photo", "source_sha256", RAW), ("crop_file", "crop_sha256", ROOT)):
            p = base / r[path_key]
            if not r.get(path_key) or not p.is_file() or sha_file(p) != r[sha_key]:
                problems.append(f"{sid}: {path_key} missing or hash changed")
    return problems


def finalize():
    if MANIFEST.exists():
        print(f"ERROR: {MANIFEST} exists (frozen); refusing to overwrite", file=sys.stderr)
        return 2
    rows = read_annotation_rows()  # list: duplicates stay visible to check_annotations
    problems = check_annotations(rows) if rows else ["no annotation rows"]
    if problems:
        print(f"PARTIAL: {len(problems)} problem(s) block finalisation:\n  " + "\n  ".join(problems[:200]), file=sys.stderr)
        return 1
    writers = sorted({r["writer_id"] for r in rows})
    others = [w for w in writers if w != M3B_WRITER]
    random.Random(SEED).shuffle(others)
    n_dev = max(1, round(DEV_FRACTION * len(writers)))
    dev = set(([M3B_WRITER] + others)[:n_dev])
    by_item = {i[0]: i for i in ITEMS}
    samples = []
    for r in sorted(rows, key=lambda r: r["sample_id"]):
        st, dev_ = r["verification_status"], r["deviation"]
        if st == "verified" and dev_ == "no":   # faithful copy: designed value, confirmed by a human
            text, value = r["prompt_text"], r["prompt_value"]
        elif st == "verified":                   # deviation: human-entered text and value (never the parser)
            text, value = r["verified_text"].strip(), str(Decimal(r["verified_value"].strip()))
        else:                                    # unresolved: kept, no value
            text, value = r.get("verified_text", "").strip(), None
        samples.append({"id": r["sample_id"], "file": r["crop_file"], "sha256": r["crop_sha256"],
                        "source_file": (RAW / r["source_photo"]).relative_to(ROOT).as_posix(),
                        "source_sha256": r["source_sha256"], "ground_truth": text, "gt_value": value,
                        "label_status": st, "deviation": dev_, "ambiguity_note": r["ambiguity_note"],
                        "unresolved_reason": r.get("unresolved_reason", ""), "category": f"custom_{r['field']}",
                        "writer_id": r["writer_id"], "group_id": r["source_photo"],
                        "pair_id": f"{r['writer_id']}_{r['item_id']}", "design_label": by_item[r["item_id"]][5],
                        "text_eligible": bool(text), "value_eligible": value is not None,
                        "punct_eligible": not r["ambiguity_note"].strip(),
                        "split": "dev" if r["writer_id"] in dev else "test", "crop_type": "template_registered"})
    pairs = {}
    for s in samples:
        pairs.setdefault(s["pair_id"], {})[s["category"]] = s["gt_value"]
    for s in samples:  # pair label from independently verified values only
        a, b = pairs[s["pair_id"]].get("custom_num"), pairs[s["pair_id"]].get("custom_words")
        s["pair_label"] = "unresolved" if a is None or b is None else ("match" if Decimal(a) == Decimal(b) else "mismatch")
    out = {"dataset": "ChequeVerify custom handwritten amounts", "seed": SEED, "dev_fraction_writers": DEV_FRACTION,
           "dev_writers": sorted(dev), "test_writers": sorted(set(writers) - dev),
           "note": "design_label/prompts are for analysis only and must never be passed to recognition",
           "samples": samples}
    MANIFEST.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(samples)} samples, writers dev={sorted(dev)} test={sorted(set(writers) - dev)}, "
          f"unresolved pairs {sum(1 for s in samples if s['pair_label'] == 'unresolved') // 2}")
    return 0


def selftest():
    lay = layout()
    assert max(b["words"][3] for b in lay["boxes"].values()) < H - MARGIN - MK - 20, "boxes overlap bottom markers"
    page = np.array(render("B", lay).convert("RGB"))[:, :, ::-1]
    big = cv2.copyMakeBorder(page, 300, 300, 300, 300, cv2.BORDER_CONSTANT, value=(200, 200, 200))
    hh, ww = big.shape[:2]
    src = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])
    dst = np.float32([[80, 40], [ww - 30, 120], [ww - 120, hh - 20], [20, hh - 90]])  # perspective + rotation
    photo = cv2.warpPerspective(big, cv2.getPerspectiveTransform(src, dst), (ww, hh), borderValue=(90, 90, 90))
    photo = cv2.resize(photo, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_AREA)
    rect, seen = rectify(photo, "B", lay)
    assert rect is not None, f"markers not found: {seen}"
    err = np.abs(rect.astype(int) - page.astype(int))[200:H - 200, 100:W - 100].mean()
    assert err < 12, f"rectification error too high: {err:.1f}"
    assert rectify(photo, "A", lay)[0] is None, "wrong-sheet photo must be rejected"
    for it in ITEMS:
        assert numeric_value(it[1]) == Decimal(it[3]) and words_value(it[2]) == Decimal(it[4]), it
    print(f"custom_sheets self-test passed (mean abs rectification error {err:.2f})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        sys.exit(extract(sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--only" else None))
    sys.exit({"make": make, "finalize": finalize, "selftest": selftest}.get(cmd, lambda: print(__doc__) or 2)() or 0)
