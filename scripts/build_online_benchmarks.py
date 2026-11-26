"""M4-ONLINE: build the online amount benchmarks (deterministic, seed 20261126). No model output is used.

  D4 cvl_numeric   GENUINE handwritten digit strings (CVL, ~120 writers): 30 writers x 10 strings, writer-disjoint
  D5 gnhk_pairs    GENUINE GNHK number words (one..twenty) + standalone GNHK integers; CONSTRUCTED cross-writer
                   match / mismatch pairs within the existing GNHK page split
  D6 syn_cheques   SYNTHETIC font-rendered cheques (HF arunchincheti/cheques_data test split): template oracle crops
                   of the numeric and words fields; NATURAL same-cheque pairs + CONSTRUCTED within-split mismatches
Ground-truth values are NOT computed with eval_metrics parsers: numerals = int(digit string); words = lookup in an
independent integer->English verbaliser table (1..99,999) or an explicit number-word table.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\build_online_benchmarks.py
"""
import hashlib
import io
import json
import random
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261126
OUT = ROOT / "data/benchmarks"
CVL_ZIP = ROOT / "data/public/cvl/cache/cvl-strings-train.zip"
GNHK_ZIP = ROOT / "data/public/gnhk/cache/test_data.zip"
SYN_ROWS = ROOT / "data/synthetic/hf_cheques/cache/rows.json"
N_CVL_WRITERS, N_CVL_DEV = 30, 9
# template oracle boxes (x0, y0, x1, y1) in the 512x256 synthetic cheques, set from per-template ink heatmaps
BOX = {"AXIS BANK": {"num": (382, 91, 493, 128), "words": (45, 78, 335, 108)},
       "HSBC": {"num": (372, 92, 505, 132), "words": (50, 100, 330, 162)},
       "Canara Bank": {"num": (400, 93, 494, 116), "words": (82, 68, 358, 100)},
       "ICICI Bank": {"num": (395, 93, 494, 123), "words": (61, 71, 340, 100)}}

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
WORDVAL = {w: i for i, w in enumerate(ONES) if i} | {TENS[i]: 10 * i for i in range(2, 10)}


def verbalize(n: int) -> str:
    """Independent int -> English (British 'and' after hundred), used only to look up GT values of word strings."""
    def below_1000(k):
        h, r = divmod(k, 100)
        parts = [ONES[h], "hundred"] if h else []
        if r:
            parts += (["and"] if h else []) + ([ONES[r]] if r < 20 else [TENS[r // 10]] + ([ONES[r % 10]] if r % 10 else []))
        return parts
    th, rest = divmod(n, 1000)
    words = (below_1000(th) + ["thousand"] if th else []) + (["and"] if th and 0 < rest < 100 else []) + below_1000(rest)
    return " ".join(words)


WORDS_TO_INT = {}
for _n in range(1, 100000):
    WORDS_TO_INT.setdefault(verbalize(_n), _n)
    WORDS_TO_INT.setdefault(verbalize(_n).replace(" and ", " "), _n)  # also without British 'and'


def norm_words(t: str) -> str:
    return " ".join(re.sub(r"[^a-z ]", " ", t.lower()).split())


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def save_png(img, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return sha(path.read_bytes())


def build_cvl():
    z = zipfile.ZipFile(CVL_ZIP)
    by_writer = {}
    for n in z.namelist():
        if n.endswith(".png"):
            label, wid, idx = n.split("/")[-1][:-4].split("-")
            by_writer.setdefault(wid, []).append((label, idx, n))
    full = sorted(w for w, v in by_writer.items() if len({l for l, _, _ in v}) == 10)
    rng = random.Random(SEED)
    rng.shuffle(full)
    chosen = full[:N_CVL_WRITERS]
    samples = []
    for k, wid in enumerate(chosen):
        for label, idx, n in sorted(by_writer[wid]):
            raw = z.read(n)
            sid = f"CVL_{label}_{wid}_{idx}"
            path = OUT / "cvl_numeric" / f"{sid}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)  # byte-identical copy of the original PNG
            samples.append({"id": sid, "file": path.relative_to(ROOT).as_posix(), "sha256": sha(raw),
                            "ground_truth": label, "gt_value": label, "label_status": "dataset_annotation_filename",
                            "category": "cvl_numeric", "genuine_handwriting": True, "writer_id": f"CVL{wid}",
                            "writer_id_basis": "inferred: 2nd filename field groups exactly one copy of each string",
                            "group_id": f"CVL{wid}", "source_archive": "cvl-strings-train.zip", "source_entry": n,
                            "split": "dev" if k < N_CVL_DEV else "test", "crop_type": "dataset_provided_image"})
    return {"dataset": "CVL Digit Strings (ICDAR 2013 HDSRC) train subset", "license": "CC-BY-NC-4.0",
            "source": "https://zenodo.org/records/1492173", "archive_md5": "123167109ed2ef554913bd0a9f4d74ba",
            "seed": SEED, "writers_available_complete": len(full), "writers_selected": N_CVL_WRITERS,
            "dev_writers": sorted(f"CVL{w}" for w in chosen[:N_CVL_DEV]), "samples": samples}


def gnhk_page_split():
    z = zipfile.ZipFile(GNHK_ZIP)
    pages = sorted(n[len("test/"):-5] for n in z.namelist() if n.endswith(".json"))
    order = pages[:]
    random.Random(SEED).shuffle(order)
    n_dev = round(0.3 * len(order))
    split = {p: ("dev" if i < n_dev else "test") for i, p in enumerate(order)}
    sub = json.loads((ROOT / "data/public/gnhk/subset/manifest.json").read_text(encoding="utf-8"))
    assert all(split[p] == v["split"] for p, v in sub["pages"].items()), "page split differs from the frozen subset"
    return z, pages, split, {s["id"] for s in sub["samples"]}


def build_gnhk_pairs():
    z, pages, split, subset_ids = gnhk_page_split()
    words, nums, cache = [], [], {}
    for p in pages:
        for k, w in enumerate(json.loads(z.read(f"test/{p}.json"))):
            t = w["text"]
            if w["type"] != "H":
                continue
            if t.lower() in WORDVAL:
                words.append((p, k, w, WORDVAL[t.lower()]))
            elif re.fullmatch(r"[0-9]{1,2}", t) and int(t) in WORDVAL.values():
                nums.append((p, k, w, int(t)))
    samples = {}

    def crop(p, k, w, value, kind):
        if p not in cache:
            cache[p] = ImageOps.exif_transpose(Image.open(io.BytesIO(z.read(f"test/{p}.jpg")))).convert("RGB")
        im = cache[p]
        xs = [w["polygon"][f"x{i}"] for i in range(4)]
        ys = [w["polygon"][f"y{i}"] for i in range(4)]
        box = (max(0, min(xs)), max(0, min(ys)), min(im.width, max(xs)), min(im.height, max(ys)))
        sid = f"GNHKP_{p}_w{k:03d}"
        path = OUT / "gnhk_pairs" / f"{sid}.png"
        samples[sid] = {"id": sid, "file": path.relative_to(ROOT).as_posix(), "sha256": save_png(im.crop(box), path),
                        "ground_truth": w["text"], "gt_value": str(value), "label_status": "dataset_annotation",
                        "category": f"gnhk_{kind}", "genuine_handwriting": True, "writer_id": None, "group_id": p,
                        "split": split[p], "crop_box_xyxy": list(box), "crop_type": "annotation_polygon_bbox",
                        "also_in_gnhk_subset_as": f"GNHK_{p}_w{k:03d}" if f"GNHK_{p}_w{k:03d}" in subset_ids else None}
        return sid
    rng = random.Random(SEED)
    pairs = []
    for sp in ("dev", "test"):
        ws = [x for x in words if split[x[0]] == sp]
        ns = [x for x in nums if split[x[0]] == sp]
        for p, k, w, v in ws:
            wid = crop(p, k, w, v, "word")
            same = [x for x in ns if x[3] == v and x[0] != p] or [x for x in ns if x[3] == v]
            diff = [x for x in ns if x[3] != v]
            for label, pool in (("match", same), ("mismatch", diff)):
                if not pool:
                    continue
                q = pool[rng.randrange(len(pool))]
                nid = crop(*q[:3], q[3], "numeric")
                pairs.append({"pair_id": f"P_{wid}_{label}", "dataset": "gnhk_pairs", "split": sp, "num_id": nid,
                              "words_id": wid, "label": label, "construction": "constructed_cross_page",
                              "genuine_handwriting": True, "num_value": str(q[3]), "words_value": str(v),
                              "parents": [q[0], p]})
    return {"dataset": "GNHK test-split number words and integers (constructed pairs)", "license": "CC-BY-4.0",
            "seed": SEED, "page_split": "identical to the frozen GNHK subset (asserted)",
            "samples": sorted(samples.values(), key=lambda s: s["id"])}, pairs


def build_synthetic():
    rows = json.loads(SYN_ROWS.read_text(encoding="utf-8"))
    order = sorted(r["row_idx"] for r in rows)
    rng = random.Random(SEED)
    rng.shuffle(order)
    n_dev = round(0.3 * len(order))
    split = {ri: ("dev" if i < n_dev else "test") for i, ri in enumerate(order)}
    samples, cheques = [], []
    for r in rows:
        src = ROOT / r["file"]
        raw = src.read_bytes()
        assert sha(raw) == r["sha256"], f"source hash changed: {src}"
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        fig, wtxt = r.get("amt_in_figures", "").strip(), r.get("amt_in_words", "").strip()
        fval = str(int(fig)) if re.fullmatch(r"[0-9]+", fig) else None
        wint = WORDS_TO_INT.get(norm_words(wtxt)) if wtxt else None
        wval = str(wint) if wint is not None else None
        cid = f"SYN_{r['row_idx']:04d}"
        ids = {}
        for field, text, val in (("num", fig, fval), ("words", wtxt, wval)):
            sid = f"{cid}_{field}"
            path = OUT / "syn_cheques" / f"{sid}.png"
            status = "dataset_annotation" if val is not None else ("blank_field" if not text else "value_unverifiable")
            samples.append({"id": sid, "file": path.relative_to(ROOT).as_posix(),
                            "sha256": save_png(im.crop(BOX[r["bank_name"]][field]), path), "ground_truth": text,
                            "gt_value": val, "label_status": status, "category": f"syn_{field}",
                            "genuine_handwriting": False, "synthetic": "font-rendered text on a scanned cheque template",
                            "writer_id": None, "group_id": cid, "pair_id": cid, "template": r["bank_name"],
                            "source_file": r["file"], "source_sha256": r["sha256"], "split": split[r["row_idx"]],
                            "crop_box_xyxy": list(BOX[r["bank_name"]][field]), "crop_type": "template_oracle_box"})
            ids[field] = sid
        cheques.append((cid, split[r["row_idx"]], ids, fval, wval))
    pairs = []
    for cid, sp, ids, fv, wv in cheques:
        label = "unresolved" if fv is None or wv is None else ("match" if fv == wv else "mismatch")
        pairs.append({"pair_id": f"P_{cid}", "dataset": "syn_cheques", "split": sp, "num_id": ids["num"],
                      "words_id": ids["words"], "label": label, "construction": "natural_same_cheque",
                      "genuine_handwriting": False, "num_value": fv, "words_value": wv, "parents": [cid]})
    for sp in ("dev", "test"):
        full = [c for c in cheques if c[1] == sp and c[3] is not None and c[4] is not None]
        perm = full[:]
        rng.shuffle(perm)
        for i, (cid, _, ids, fv, _) in enumerate(full):
            for j in range(len(perm)):  # first partner in the seeded order with a different words value
                o = perm[(i + j + 1) % len(perm)]
                if o[0] != cid and o[4] != fv:
                    pairs.append({"pair_id": f"P_{cid}_x_{o[0]}", "dataset": "syn_cheques", "split": sp,
                                  "num_id": ids["num"], "words_id": o[2]["words"], "label": "mismatch",
                                  "construction": "constructed_cross_cheque", "genuine_handwriting": False,
                                  "num_value": fv, "words_value": o[4], "parents": [cid, o[0]]})
                    break
    return {"dataset": "SYNTHETIC cheques: HF arunchincheti/cheques_data test split (cheque rows)",
            "license": "Apache-2.0 (declared on the HF card; underlying template provenance undocumented)",
            "revision": "cd9902644033cc2114a240743d94309e5ac26bd2", "seed": SEED,
            "split_unit": "cheque (no writers; templates shared across splits)", "boxes": BOX,
            "samples": samples}, pairs


def main():
    for name in ("cvl_numeric", "gnhk_pairs", "syn_cheques"):
        if (OUT / name / "manifest.json").exists():
            raise SystemExit(f"{OUT / name / 'manifest.json'} exists; refusing to overwrite a frozen manifest")
    cvl = build_cvl()
    gn, gpairs = build_gnhk_pairs()
    syn, spairs = build_synthetic()
    for name, m in (("cvl_numeric", cvl), ("gnhk_pairs", gn), ("syn_cheques", syn)):
        (OUT / name / "manifest.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    pairs = gpairs + spairs
    (OUT / "amount_pairs.json").write_text(json.dumps({"seed": SEED, "pairs": pairs}, indent=2), encoding="utf-8")
    c = lambda xs, k: {v: sum(1 for x in xs if x[k] == v) for v in sorted({x[k] for x in xs}, key=str)}
    print("cvl", len(cvl["samples"]), c(cvl["samples"], "split"))
    print("gnhk_pairs samples", len(gn["samples"]), c(gn["samples"], "split"), "pairs", len(gpairs), c(gpairs, "label"))
    print("syn samples", len(syn["samples"]), c(syn["samples"], "split"), c(syn["samples"], "label_status"))
    print("syn pairs", len(spairs), c(spairs, "label"), c(spairs, "construction"), c(spairs, "split"))


if __name__ == "__main__":
    assert verbalize(3083) == "three thousand and eighty three" and verbalize(462) == "four hundred and sixty two"
    assert WORDS_TO_INT["three thousand and eighty three"] == 3083 and WORDS_TO_INT["eight thousand three hundred ninety five"] == 8395
    main()
