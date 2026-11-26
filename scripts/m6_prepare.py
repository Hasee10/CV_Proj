"""M6 preparation (no inference): stress variants and diagnostic images, as frozen in artifacts/M6/EXPERIMENT_PROTOCOL.md.

  data/stress/m6_parents.json            245 recognition-eligible dev entries (from the frozen manifests)
  data/stress/m6_dev/                     3,675 variants + manifest.json (scripts/stress_corrupt.py, unchanged parameters)
  data/stress/m6_pilot_ids.json           pilot = variants of the first 2 eligible dev entries per dataset by sorted id
  data/diagnostics/m6/manifest.json       DX-B (2x, 4x), DX-C (word segments 1x/2x), DX-D (line-removed 1x/2x, original 2x)
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m6_prepare.py
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_baseline as rb  # noqa: E402
import stress_corrupt as sc  # noqa: E402

STRESS, DIAG = ROOT / "data/stress", ROOT / "data/diagnostics/m6"
_spec = importlib.util.spec_from_file_location("upstream_transforms", rb.si.UPSTREAM / "comer/datamodule/transforms.py")
_tf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tf)
UPSTREAM_SCALE = _tf.ScaleToLimitRange(w_lo=16, w_hi=1024, h_lo=16, h_hi=256)   # the upstream test-time resize


def effective_hw(img):
    return list(UPSTREAM_SCALE(img).shape[:2])


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def otsu_ink(grey):
    _, ink = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return ink > 0


def line_masks(ink, h_frac=0.4, v_frac=0.7):
    h, w = ink.shape
    u8 = ink.astype(np.uint8) * 255
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, int(w * h_frac)), 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, int(h * v_frac))))
    return cv2.morphologyEx(u8, cv2.MORPH_OPEN, hk) > 0, cv2.morphologyEx(u8, cv2.MORPH_OPEN, vk) > 0


def remove_lines(rgb):
    """DX-D: long horizontal / vertical printed lines -> background median. Returns (image, removed_pixel_count)."""
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ink = otsu_ink(grey)
    hl, vl = line_masks(ink)
    lines = cv2.dilate((hl | vl).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    bg = np.median(rgb[~ink], axis=0) if (~ink).any() else np.array([255, 255, 255])
    out = rgb.copy()
    out[lines] = bg.astype(np.uint8)
    return out, int(lines.sum())


def segment_words(rgb):
    """DX-C oracle-validated geometric segmentation: lines on empty rows, words on column gaps >= 0.5 x median ink height."""
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    ink = otsu_ink(grey)
    hl, _ = line_masks(ink)
    ink = ink & ~(cv2.dilate(hl.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    rows = ink.sum(1)
    bands, start = [], None
    for y, v in enumerate(list(rows) + [0]):
        if v > 0 and start is None:
            start = y
        elif v == 0 and start is not None:
            bands.append((start, y))
            start = None
    total = ink.sum() or 1
    bands = [b for b in bands if ink[b[0]:b[1]].sum() >= 0.03 * total]
    boxes = []
    for y0, y1 in bands:
        band = ink[y0:y1]
        ys = np.nonzero(band)[0]
        c0, c1 = (int(np.percentile(ys, 25)), int(np.percentile(ys, 75)) + 1) if len(ys) else (0, band.shape[0])
        cols = band[c0:c1].sum(0)  # amendment A2: gaps measured in the central text zone only
        heights = [np.ptp(np.nonzero(band[:, x])[0]) + 1 for x in range(band.shape[1]) if cols[x]]
        gap_min = max(2, int(0.5 * float(np.median(heights)))) if heights else 2
        x, w = 0, band.shape[1]
        segs, s, gap = [], None, 0
        for x in range(w + 1):
            on = x < w and cols[x] > 0
            if on:
                if s is None:
                    s = x
                gap = 0
                last = x
            elif s is not None:
                gap += 1
                if gap >= gap_min or x == w:
                    segs.append((s, last + 1))
                    s, gap = None, 0
        for xs, xe in segs:
            boxes.append((max(0, xs - 2), max(0, y0 - 2), min(rgb.shape[1], xe + 2), min(rgb.shape[0], y1 + 2)))
    return boxes


def up(rgb, k):
    return cv2.resize(rgb, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)


def save(rgb, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    assert cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)), path
    return sha(path)


def main():
    if (DIAG / "manifest.json").exists():
        raise SystemExit("diagnostic manifest exists; refusing to overwrite")
    dev = sorted([e for e in rb.load_entries("dev") if e["ground_truth"]], key=lambda e: e["id"])
    parents = [{k: v for k, v in e.items()} for e in dev]
    STRESS.mkdir(parents=True, exist_ok=True)
    (STRESS / "m6_parents.json").write_text(json.dumps({"samples": parents}, indent=1, ensure_ascii=False), encoding="utf-8")
    if (STRESS / "m6_dev" / "manifest.json").exists():  # stress set already generated: reuse, never regenerate
        rows = json.loads((STRESS / "m6_dev" / "manifest.json").read_text(encoding="utf-8"))["samples"]
        assert len(rows) == 15 * len(parents)
    else:
        rows, probs = sc.generate(STRESS / "m6_parents.json", "dev", STRESS / "m6_dev", root=ROOT)
        assert not probs, probs
    pilot_parents = [e["id"] for ds in ("D1", "D4", "D5", "D6") for e in [x for x in dev if x["dataset"] == ds][:2]]
    (STRESS / "m6_pilot_ids.json").write_text(json.dumps([r["id"] for r in rows if r["parent_id"] in pilot_parents]), encoding="utf-8")

    def first(sel, n=8):
        return [e for e in dev if sel(e)][:n]
    dxb = (first(lambda e: e["dataset"] == "D1") + first(lambda e: e["dataset"] == "D4")
           + first(lambda e: e["category"] == "syn_num") + first(lambda e: e["category"] == "syn_words"))
    dxc = first(lambda e: e["category"] == "syn_words")
    lined = {"AXIS BANK", "Canara Bank", "ICICI Bank"}
    dxd = first(lambda e: e["category"] == "syn_num" and e["template"] in lined) + \
        first(lambda e: e["category"] == "syn_words" and e["template"] in lined)
    diag = []

    def add(parent, cond, rgb, extra=None):
        did = f"{parent['id']}__{cond}"
        path = DIAG / f"{did}.png"
        diag.append({"id": did, "parent_id": parent["id"], "condition": cond, "dataset": parent["dataset"],
                     "category": parent["category"], "template": parent.get("template"), "group_id": parent["group_id"],
                     "ground_truth": parent["ground_truth"], "gt_value": parent.get("gt_value"), "split": "dev",
                     "file": path.relative_to(ROOT).as_posix(), "sha256": save(rgb, path),
                     "raw_hw": list(rgb.shape[:2]), "effective_hw": effective_hw(rgb), **(extra or {})})
    rgb_of = lambda e: cv2.cvtColor(cv2.imread(str(ROOT / e["file"])), cv2.COLOR_BGR2RGB)
    for e in dxb:
        img = rgb_of(e)
        for k in (2, 4):
            add(e, f"DXB_up{k}", up(img, k), {"diagnostic": "DX-B", "scale": k, "interpolation": "INTER_CUBIC"})
    for e in dxc:
        img = rgb_of(e)
        boxes = segment_words(img)
        n_gt = len(e["ground_truth"].split())
        for k in (1, 2):
            for i, (x0, y0, x1, y1) in enumerate(boxes):
                crop = img[y0:y1, x0:x1]
                add(e, f"DXC_seg{k}x_w{i:02d}", up(crop, k) if k > 1 else crop,
                    {"diagnostic": "DX-C", "scale": k, "word_index": i, "segments": len(boxes), "gt_words": n_gt,
                     "segmentation_matches_gt_count": len(boxes) == n_gt, "box_xyxy": [x0, y0, x1, y1]})
    for e in dxd:
        img = rgb_of(e)
        clean, removed = remove_lines(img)
        add(e, "DXD_orig2x", up(img, 2), {"diagnostic": "DX-D", "scale": 2})
        add(e, "DXD_clean1x", clean, {"diagnostic": "DX-D", "scale": 1, "removed_pixels": removed})
        add(e, "DXD_clean2x", up(clean, 2), {"diagnostic": "DX-D", "scale": 2, "removed_pixels": removed})
    sanity = [{"id": e["id"], "dataset": e["dataset"], "raw_hw": list(rgb_of(e).shape[:2]), "effective_hw": effective_hw(rgb_of(e))}
              for e in dxb]
    (DIAG / "manifest.json").write_text(json.dumps({"subsets": {"DX-B": [e["id"] for e in dxb], "DX-C": [e["id"] for e in dxc],
                                                                "DX-D": [e["id"] for e in dxd]},
                                                    "original_dims": sanity, "samples": diag}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"parents {len(parents)}, variants {len(rows)}, pilot variants {len(json.loads((STRESS / 'm6_pilot_ids.json').read_text()))}, "
          f"diagnostic images {len(diag)} (DX-B {sum(d['diagnostic'] == 'DX-B' for d in diag)}, DX-C {sum(d['diagnostic'] == 'DX-C' for d in diag)}, "
          f"DX-D {sum(d['diagnostic'] == 'DX-D' for d in diag)}); DX-C segmentation matches GT word count: "
          f"{sum(1 for e in dxc if any(d['parent_id'] == e['id'] and d.get('segmentation_matches_gt_count') for d in diag))}/{len(dxc)}")


if __name__ == "__main__":
    main()
