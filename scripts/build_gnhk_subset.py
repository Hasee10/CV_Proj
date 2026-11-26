"""Deterministic GNHK test-set word subset with page-disjoint dev/test split (M4).

Rule (fixed before any inference, independent of model output):
  1. Split the 172 official TEST pages: sort page ids, shuffle with SEED, first 30% -> dev, rest -> test.
  2. Eligible words: type 'H' (handwritten), not a %special% token, every character in SSL_HWD_Dict.txt.
  3. Per split, shuffle eligible words with SEED and take the first N per stratum
     (digit-containing / other), at most PAGE_CAP words per page.
  4. Crop = axis-aligned bounding box of the official word polygon on the EXIF-transposed page. No margin,
     no enhancement. These are annotation (oracle) crops, not an automatic segmentation method.
Usage: .venv\\Scripts\\python.exe -I scripts\\build_gnhk_subset.py
"""
import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "data" / "public" / "gnhk" / "cache" / "test_data.zip"
ZIP_SHA256 = "6f3d65d91535d1665050afd83a9f3831394d80accfae88c5b91bbb990781eacb"
OUT = ROOT / "data" / "public" / "gnhk" / "subset"
DICT = ROOT / "third_party" / "LoGoHTR" / "comer" / "datamodule" / "SSL_HWD_Dict.txt"
SEED, DEV_FRACTION, PAGE_CAP = 20261126, 0.3, 3
TARGETS = {"dev": {"digit": 20, "other": 60}, "test": {"digit": 40, "other": 120}}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main():
    raw = ZIP.read_bytes()
    assert sha(raw) == ZIP_SHA256, "test_data.zip hash mismatch; rerun fetch_gnhk_test.py"
    z = zipfile.ZipFile(io.BytesIO(raw))
    charset = {l.strip() for l in DICT.read_text(encoding="utf-8").splitlines()} - {""}
    pages = sorted(n[len("test/"):-5] for n in z.namelist() if n.endswith(".json"))
    order = pages[:]
    random.Random(SEED).shuffle(order)
    n_dev = round(DEV_FRACTION * len(order))
    page_split = {p: ("dev" if i < n_dev else "test") for i, p in enumerate(order)}

    eligible, counts = [], {"words": 0, "printed": 0, "special": 0, "out_of_vocab": 0, "eligible": 0}
    for p in pages:
        for k, w in enumerate(json.loads(z.read(f"test/{p}.json"))):
            counts["words"] += 1
            t = w["text"]
            if w["type"] != "H":
                counts["printed"] += 1
            elif t.startswith("%") and t.endswith("%"):
                counts["special"] += 1
            elif not t or any(c not in charset for c in t):
                counts["out_of_vocab"] += 1
            else:
                counts["eligible"] += 1
                eligible.append({"page": p, "idx": k, "text": t, "polygon": w["polygon"], "line_idx": w["line_idx"],
                                 "stratum": "digit" if any(c.isdigit() for c in t) else "other"})

    rng = random.Random(SEED)
    rng.shuffle(eligible)
    chosen, per_page = [], {}
    for split, strata in TARGETS.items():
        for stratum, n in strata.items():
            got = 0
            for w in eligible:
                if got == n:
                    break
                if page_split[w["page"]] == split and w["stratum"] == stratum and per_page.get(w["page"], 0) < PAGE_CAP:
                    per_page[w["page"]] = per_page.get(w["page"], 0) + 1
                    chosen.append({**w, "split": split})
                    got += 1
            assert got == n, f"only {got}/{n} for {split}/{stratum}"

    OUT.mkdir(parents=True, exist_ok=True)
    pages_meta, samples, cache = {}, [], {}
    for w in sorted(chosen, key=lambda w: (w["page"], w["idx"])):
        p = w["page"]
        if p not in cache:
            jpg = z.read(f"test/{p}.jpg")
            im = Image.open(io.BytesIO(jpg))
            orient = im.getexif().get(0x0112)
            cache[p] = ImageOps.exif_transpose(im).convert("RGB")
            pages_meta[p] = {"source_file": f"test/{p}.jpg", "sha256": sha(jpg), "exif_orientation": orient,
                             "transposed_size": list(cache[p].size), "split": page_split[p]}
        im = cache[p]
        xs = [w["polygon"][f"x{i}"] for i in range(4)]
        ys = [w["polygon"][f"y{i}"] for i in range(4)]
        box = (max(0, min(xs)), max(0, min(ys)), min(im.width, max(xs)), min(im.height, max(ys)))
        assert box[2] > box[0] and box[3] > box[1], f"degenerate box {p}#{w['idx']}"
        sid = f"GNHK_{p}_w{w['idx']:03d}"
        path = OUT / f"{sid}.png"
        im.crop(box).save(path)
        samples.append({"id": sid, "file": f"data/public/gnhk/subset/{sid}.png", "sha256": sha(path.read_bytes()),
                        "ground_truth": w["text"], "category": f"gnhk_{w['stratum']}", "stratum": w["stratum"],
                        "split": w["split"], "group_id": p, "writer_id": None, "region": p.split("_")[1],
                        "line_idx": w["line_idx"], "crop_box_xyxy": list(box), "crop_type": "annotation_polygon_bbox"})
    manifest = {
        "dataset": "GNHK test split (Lee, Chung, Lee, ICDAR 2021), word subset",
        "license": "CC-BY-4.0 (github.com/GoodNotes/GNHK-dataset)",
        "source": "https://huggingface.co/datasets/staghado/GNHK-Dataset (mirror; official goodnotes.com/gnhk no longer serves data)",
        "source_revision": "eaa67d396fd29b8b04e38d630da79f67db11b212",
        "archive": {"name": "test_data.zip", "sha256": ZIP_SHA256, "bytes": len(raw), "crc32": 1897843626},
        "selection_rule": __doc__.strip().splitlines()[2:9], "seed": SEED, "dev_fraction_pages": DEV_FRACTION,
        "page_cap": PAGE_CAP, "targets": TARGETS, "counts": counts,
        "pages_total": len(pages), "pages_dev": n_dev, "pages_test": len(pages) - n_dev,
        "writer_ids": "not provided by GNHK; page id used as group id (writer-disjointness NOT verifiable)",
        "pages": pages_meta, "samples": samples}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    by = {s: sum(x["split"] == s for x in samples) for s in TARGETS}
    print(counts, "selected", len(samples), by, "pages used", len(pages_meta))


if __name__ == "__main__":
    main()
