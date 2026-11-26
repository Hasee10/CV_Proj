"""Labelled contact sheet for the M4-ONLINE benchmarks (review aid; deterministic selection, no model output).
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\m4_online_contact_sheet.py artifacts\\M4_ONLINE\\CONTACT_SHEET.png
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "data/benchmarks"


def font(n):
    try:
        return ImageFont.truetype("arial.ttf", n)
    except OSError:
        return ImageFont.load_default(n)


def tile(path, w, h):
    im = Image.open(ROOT / path).convert("RGB")
    im.thumbnail((w, h))
    return im


def main():
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit(f"{out} exists; refusing to overwrite")
    man = {n: {s["id"]: s for s in json.loads((B / n / "manifest.json").read_text(encoding="utf-8"))["samples"]}
           for n in ("cvl_numeric", "gnhk_pairs", "syn_cheques")}
    pairs = json.loads((B / "amount_pairs.json").read_text(encoding="utf-8"))["pairs"]
    W, rows, f, fb = 1400, [], font(15), font(20)
    canvas = Image.new("RGB", (W, 3600), "white")
    d = ImageDraw.Draw(canvas)
    y = 10

    def header(t):
        nonlocal y
        d.text((10, y), t, font=fb, fill=(160, 0, 0))
        y += 32
    header("A. GENUINE handwriting - CVL Digit Strings (CC-BY-NC-4.0): one dev and one test writer per string")
    cvl = list(man["cvl_numeric"].values())
    picks = []
    for label in sorted({s["ground_truth"] for s in cvl}):
        for sp in ("dev", "test"):
            picks.append(next(s for s in cvl if s["ground_truth"] == label and s["split"] == sp))
    for i, s in enumerate(picks):
        x, yy = (i % 5) * 280 + 10, y + (i // 5) * 78
        canvas.paste(tile(s["file"], 260, 50), (x, yy))
        d.text((x, yy + 52), f"GT {s['ground_truth']}  {s['writer_id']} [{s['split']}]", font=f, fill="blue")
    y += ((len(picks) + 4) // 5) * 78 + 10
    header("B. GENUINE handwriting - GNHK number words vs integers (CC-BY-4.0): CONSTRUCTED cross-page pairs")
    gp = [p for p in pairs if p["dataset"] == "gnhk_pairs"]
    for i, p in enumerate(gp):
        n, wd = man["gnhk_pairs"][p["num_id"]], man["gnhk_pairs"][p["words_id"]]
        x, yy = (i % 4) * 350 + 10, y + (i // 4) * 66
        canvas.paste(tile(n["file"], 90, 44), (x, yy))
        canvas.paste(tile(wd["file"], 160, 44), (x + 95, yy))
        d.text((x, yy + 46), f"{n['ground_truth']!r} vs {wd['ground_truth']!r} -> {p['label']} [{p['split']}]", font=f,
               fill="green" if p["label"] == "match" else "red")
    y += ((len(gp) + 3) // 4) * 66 + 10
    header("C. SYNTHETIC font-rendered cheques (HF arunchincheti/cheques_data): template oracle crops")
    sp = [p for p in pairs if p["dataset"] == "syn_cheques"]
    groups = [("natural match", [p for p in sp if p["construction"].startswith("natural") and p["label"] == "match"][:6]),
              ("natural mismatch (in source data)", [p for p in sp if p["construction"].startswith("natural") and p["label"] == "mismatch"][:6]),
              ("constructed mismatch", [p for p in sp if p["construction"].startswith("constructed")][:6]),
              ("unresolved (blank field)", [p for p in sp if p["label"] == "unresolved"][:6])]
    for title, ps in groups:
        d.text((10, y), title, font=fb, fill=(0, 0, 120))
        y += 28
        for i, p in enumerate(ps):
            n, wd = man["syn_cheques"][p["num_id"]], man["syn_cheques"][p["words_id"]]
            x, yy = (i % 2) * 700 + 10, y + (i // 2) * 84
            canvas.paste(tile(n["file"], 150, 50), (x, yy))
            canvas.paste(tile(wd["file"], 500, 60), (x + 160, yy))
            d.text((x, yy + 62), f"{p['pair_id']}: num={p['num_value']} words={p['words_value']} -> {p['label']} [{p['split']}]",
                   font=f, fill="black")
        y += ((len(ps) + 1) // 2) * 84 + 6
    canvas.crop((0, 0, W, y + 10)).save(out)
    print(f"wrote {out} ({W}x{y + 10})")


if __name__ == "__main__":
    main()
