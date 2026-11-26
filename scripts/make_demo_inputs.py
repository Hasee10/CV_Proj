"""Build the demo sheets in data/demo/ from tracked DEV-split crops (no test data, no new images).

Each sheet pastes one numeric-amount crop and one written-amount crop onto a white page and records the exact
normalised ROIs, so the full-image /api/verify flow can be shown without a real cheque. These are constructed
composites, not cheques; the pairs are chosen to show each decision type, not to represent benchmark accuracy.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\make_demo_inputs.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_baseline as rb  # noqa: E402

OUT = ROOT / "data/demo"
LICENCE = {"D4": "CVL digit strings, CC-BY-NC-4.0", "D5": "GNHK, CC-BY-4.0",
           "D6": "HF arunchincheti/cheques_data, Apache-2.0 (declared); SYNTHETIC font-rendered text"}
SHEETS = {
    "sheet_accept": ("GNHKP_eng_EU_310_w021", "GNHKP_eng_EU_117_w051", "genuine handwriting, constructed pair (two GNHK pages): 1 / one"),
    "sheet_flag": ("CVL_25000_0021_08", "GNHKP_eng_EU_117_w051", "genuine handwriting, constructed MISMATCH: 25000 / one"),
    "sheet_review": ("SYN_0001_num", "SYN_0001_words", "SYNTHETIC cheque fields from one synthetic cheque: 3083 / Three Thousand and Eighty Three"),
}


def main():
    ent = {e["id"]: e for e in rb.load_entries("dev")}
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"note": __doc__.split("Usage")[0].strip(), "split": "dev", "sheets": {}}
    for name, (num_id, wr_id, desc) in SHEETS.items():
        a, b = (np.array(Image.open(ROOT / ent[i]["file"]).convert("RGB")) for i in (num_id, wr_id))
        W = max(900, 80 + b.shape[1] + 60 + a.shape[1])
        H = 60 + max(a.shape[0], 1) + 40 + b.shape[0] + 60
        page = np.full((H, W, 3), 255, np.uint8)
        na = (W - 40 - a.shape[1], 40)                    # numeric box top-right, like a cheque amount box
        wb = (40, 40 + a.shape[0] + 40)                   # written line below, left
        page[na[1]:na[1] + a.shape[0], na[0]:na[0] + a.shape[1]] = a
        page[wb[1]:wb[1] + b.shape[0], wb[0]:wb[0] + b.shape[1]] = b
        Image.fromarray(page).save(OUT / f"{name}.png")
        box = lambda o, im: [o[0], o[1], o[0] + im.shape[1], o[1] + im.shape[0]]
        manifest["sheets"][name] = {
            "file": f"data/demo/{name}.png", "size_wh": [W, H], "description": desc,
            "numeric": {"source_id": num_id, "ground_truth": ent[num_id]["ground_truth"], "licence": LICENCE[ent[num_id]["dataset"]],
                        "box_px": box(na, a), "roi": [round(v, 6) for v in (na[0] / W, na[1] / H, (na[0] + a.shape[1]) / W, (na[1] + a.shape[0]) / H)]},
            "written": {"source_id": wr_id, "ground_truth": ent[wr_id]["ground_truth"], "licence": LICENCE[ent[wr_id]["dataset"]],
                        "box_px": box(wb, b), "roi": [round(v, 6) for v in (wb[0] / W, wb[1] / H, (wb[0] + b.shape[1]) / W, (wb[1] + b.shape[0]) / H)]}}
    (OUT / "demo_manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: (v["size_wh"], v["numeric"]["roi"], v["written"]["roi"]) for k, v in manifest["sheets"].items()}))


if __name__ == "__main__":
    main()
