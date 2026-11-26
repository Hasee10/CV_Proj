"""M3-B: neutral crops + frozen manifest for the student's handwritten photographs.

Only operations: EXIF-orientation check (none present), rectangular crop with recorded pixel
boxes (chosen by visual inspection BEFORE inference), lossless PNG save. No enhancement.
Usage: .venv\\Scripts\\python.exe -I scripts\\make_handwritten_crops.py
"""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "handwritten_examples" / "raw"
CROPS = ROOT / "data" / "handwritten_examples" / "crops"

# photo, id, ground truth (as actually written), category, crop box (x0, y0, x1, y1), notes
SAMPLES = [
    ("sample_example1.jpeg", "H01", "2500", "numeric", (540, 310, 940, 455), ""),
    ("sample_example2.jpeg", "H02", "12500", "numeric", (110, 270, 680, 435), ""),
    ("sample_example3.jpeg", "H03", "50000", "numeric", (360, 140, 930, 350),
     "Intended list had '50,000'; photo has no comma."),
    ("sample_example4.jpeg", "H04", "1250.00", "numeric_decimal", (260, 225, 1240, 410),
     "Intended list had '1,250.00'; photo has no comma. AMBIGUOUS: decimal point is drawn as a short "
     "horizontal stroke and could be read as '-'; ground truth follows writer intent '.'."),
    ("sample_example5.jpeg", "H05", "75,450.50", "numeric_comma_decimal", (130, 140, 1305, 415), ""),
    ("sample_example6.jpeg", "H06", "Twenty", "word", (500, 40, 1095, 305), ""),
    ("sample_example7.jpeg", "H07", "Thousand", "word", (255, 115, 1265, 385), ""),
    ("sample_example8.jpeg", "H08", "Rupees", "word", (190, 100, 660, 320), ""),
    ("sample_example9.jpeg", "H09", "Five thousand only", "multiword", (190, 60, 1455, 325),
     "Intended list had 'Five Thousand Only'; photo uses lowercase 't' and 'o'. "
     "AMBIGUOUS spacing: the gap between 'Five' and 'thousand' is very narrow."),
]
# Separately segmented words of H09 (reported apart from full-line results).
SEGMENTS = [
    ("sample_example9.jpeg", "H09a", "Five", "segmented_word", (190, 60, 443, 325),
     "Cut at x=443 between 'e' and 't'; the 't' crossbar may be partially clipped."),
    ("sample_example9.jpeg", "H09b", "thousand", "segmented_word", (443, 60, 1060, 325), ""),
    ("sample_example9.jpeg", "H09c", "only", "segmented_word", (1100, 60, 1455, 325), ""),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    CROPS.mkdir(parents=True, exist_ok=True)
    photos, entries = {}, []
    for photo, sid, gt, cat, box, note in SAMPLES + SEGMENTS:
        src = RAW / photo
        im = Image.open(src)
        orient = im.getexif().get(0x0112)
        assert orient in (None, 1), f"{photo}: EXIF orientation {orient} needs handling"
        photos[photo] = {"file": f"data/handwritten_examples/raw/{photo}", "format": im.format, "mode": im.mode,
                         "size": list(im.size), "exif_orientation": orient, "sha256": sha(src)}
        x0, y0, x1, y1 = box
        assert 0 <= x0 < x1 <= im.size[0] and 0 <= y0 < y1 <= im.size[1], f"{sid}: box outside image"
        out = CROPS / f"{sid}.png"
        im.convert("RGB").crop(box).save(out)
        base = {"ground_truth": gt, "category": cat, "photo": photo, "notes": note}
        entries.append({"id": sid, "condition": "segmented_word" if cat == "segmented_word" else "crop",
                        "file": f"data/handwritten_examples/crops/{out.name}", "crop_box_xyxy": list(box),
                        "sha256": sha(out), **base})
        if cat != "segmented_word":
            entries.append({"id": f"{sid}-full", "condition": "full_photo", "file": photos[photo]["file"],
                            "crop_box_xyxy": None, "sha256": photos[photo]["sha256"], **base})
    order = {"crop": 0, "full_photo": 1, "segmented_word": 2}
    entries.sort(key=lambda e: (order[e["condition"]], e["id"]))
    manifest = {
        "description": "M3-B independent handwriting samples, written and photographed by the student (consented, no bank data).",
        "ground_truth_rule": "Transcription of what is actually written (verified visually against each photo), not the intended list.",
        "intended_list_from_student": ["01: 2500", "02: 12500", "03: 1,250.00", "04: 50,000", "05: 75,450.50",
                                       "07: Thousand", "08: Rupees", "09: Twenty", "10: Five Thousand Only"],
        "processing": "EXIF orientation checked (none present); rectangular crop with recorded box; saved as PNG. No enhancement.",
        "conditions": {"crop": "primary: neutral crop isolating the sample",
                       "full_photo": "secondary: unmodified original photo",
                       "segmented_word": "separate: individual words cropped from H09; not counted as full-line recognition"},
        "photos": photos, "samples": entries}
    (ROOT / "data" / "handwritten_examples" / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{len(photos)} photos, {len(entries)} manifest entries")


if __name__ == "__main__":
    main()
