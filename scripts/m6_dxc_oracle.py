"""DX-C oracle word crops from AI visual review (amendment A2: geometric segmentation matched 0/8 lines).

Boxes (x0, y0, x1, y1) in original crop pixels were read from a magnified, ruled rendering of each line before any
DX-C recognition. They are ORACLE diagnostic regions, not an automatic algorithm; touching cursive words (SYN_0037,
SYN_0051) have approximate boundaries. Ground-truth words are never passed to recognition.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m6_dxc_oracle.py
"""
import hashlib
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import m6_prepare as mp  # noqa: E402

L1, L2, FULL = (4, 32), (36, 60), (0, 32)
BOXES = {  # parent id -> list of (x0, x1, (y0, y1))
    "SYN_0001_words": [(12, 44, L1), (47, 99, L1), (101, 118, L1), (123, 158, L1), (2, 36, L2)],
    "SYN_0013_words": [(7, 29, FULL), (32, 80, FULL), (82, 116, FULL), (117, 161, FULL), (162, 181, FULL), (184, 218, FULL), (218, 250, FULL)],
    "SYN_0031_words": [(4, 37, FULL), (36, 89, FULL), (90, 124, FULL), (124, 174, FULL), (174, 198, FULL), (199, 238, FULL)],
    "SYN_0032_words": [(8, 21, FULL), (21, 51, FULL), (51, 70, FULL), (70, 98, FULL), (99, 112, FULL), (112, 135, FULL)],
    "SYN_0036_words": [(4, 28, FULL), (31, 79, FULL), (81, 99, FULL), (101, 149, FULL), (152, 171, FULL), (174, 208, FULL), (209, 231, FULL)],
    "SYN_0037_words": [(2, 31, FULL), (32, 86, FULL), (84, 105, FULL), (107, 151, FULL), (151, 186, FULL)],
    "SYN_0042_words": [(12, 45, L1), (47, 101, L1), (101, 126, L1), (127, 174, L1), (2, 24, L2), (26, 61, L2), (62, 98, L2)],
    "SYN_0051_words": [(2, 38, FULL), (36, 91, FULL), (90, 120, FULL), (120, 172, FULL), (171, 192, FULL), (192, 231, FULL)],
}


def main():
    out = mp.DIAG / "dxc_oracle_manifest.json"
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite")
    man = {s["id"]: s for s in json.loads((ROOT / "data/benchmarks/syn_cheques/manifest.json").read_text(encoding="utf-8"))["samples"]}
    rows = []
    for pid, boxes in BOXES.items():
        p = man[pid]
        img = cv2.cvtColor(cv2.imread(str(ROOT / p["file"])), cv2.COLOR_BGR2RGB)
        assert len(boxes) == len(p["ground_truth"].split()), pid  # geometry check only
        for k in (1, 2):
            for i, (x0, x1, (y0, y1)) in enumerate(boxes):
                crop = img[max(0, y0):min(img.shape[0], y1), max(0, x0 - 1):min(img.shape[1], x1 + 1)]
                crop = mp.up(crop, k) if k > 1 else crop
                did = f"{pid}__DXC_oracle{k}x_w{i:02d}"
                path = mp.DIAG / f"{did}.png"
                rows.append({"id": did, "parent_id": pid, "condition": f"DXC_oracle{k}x", "diagnostic": "DX-C", "scale": k,
                             "word_index": i, "segments": len(boxes), "dataset": "D6", "category": "syn_words",
                             "template": p["template"], "group_id": p["group_id"], "ground_truth": p["ground_truth"],
                             "gt_value": p["gt_value"], "split": "dev", "box_x0x1y0y1": [x0, x1, y0, y1],
                             "segmentation": "oracle_visual (AI-reviewed, not automatic)",
                             "file": path.relative_to(ROOT).as_posix(), "sha256": mp.save(crop, path)})
    out.write_text(json.dumps({"samples": rows}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(rows)} oracle word crops for {len(BOXES)} lines")


if __name__ == "__main__":
    main()
