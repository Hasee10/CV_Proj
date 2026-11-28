"""Compose opening-gallery plates from saved DEV evidence; never run inference."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC, OUT = ROOT / "public", ROOT / "public/gallery"
OUT.mkdir(exist_ok=True)
latest = json.loads((PUBLIC / "results/latest.json").read_text())
manifest = json.loads((PUBLIC / latest["manifest"].lstrip("/")).read_text())
records = {r["id"]: r for r in manifest["records"]}

def response(key):
    return json.loads((PUBLIC / records[key]["response"].lstrip("/")).read_text())

def font(size, weight=450):
    value = ImageFont.truetype(str(PUBLIC / "fonts/Manrope.ttf"), size)
    value.set_variation_by_axes([weight])
    return value

INK, MUTED, LINE = "#332e33", "#746d70", "#d4c9bd"

def text(x, y, value, size=32, fill=INK, weight=450):
    draw.text((x, y), str(value), font=font(size, weight), fill=fill)

def begin(index, title, color):
    global image, draw
    image = Image.new("RGB", (1200, 1500), color)
    draw = ImageDraw.Draw(image)
    text(74, 55, "CHEQUEVERIFY / RECORDED EVIDENCE", 23, MUTED, 650)
    text(1015, 55, f"0{index}/06", 23, MUTED)
    draw.line((74, 112, 1126, 112), fill=LINE, width=2)
    for i, line in enumerate(title):
        text(70, 165 + i * 100, line, 86, INK, 500)

def source(key, field=None):
    value = Image.open(PUBLIC / records[key]["image"].lstrip("/")).convert("RGB")
    if field:
        value = value.crop(response(key)["rois"][field + "_px"])
    return value

def crop_plate(key, field, box):
    draw.rounded_rectangle(box, radius=5, fill="#fffdf8", outline=LINE, width=2)
    value = source(key, field)
    x0, y0, x1, y1 = box
    scale = min((x1-x0-100)/value.width, (y1-y0-80)/value.height)
    value = value.resize((round(value.width*scale), round(value.height*scale)), Image.Resampling.LANCZOS)
    image.paste(value, (round((x0+x1-value.width)/2), round((y0+y1-value.height)/2)))

def finish(name, source_note):
    draw.line((74, 1370, 1126, 1370), fill=LINE, width=2)
    text(74, 1400, source_note, 24, MUTED)
    image.save(OUT / name, optimize=True)

accept, base, athn, review = (response(k) for k in ("sheet_accept", "numeric-baseline", "numeric-proposed", "sheet_review"))
begin(2, ["Two fields.", "One amount."], "#f5ead5")
for field, y, label in [("numeric", 440, "FIGURES"), ("written", 860, "WORDS")]:
    text(74, y-50, label, 26, MUTED, 600)
    crop_plate("sheet_accept", field, (74, y, 790, y+280))
    text(850, y+95, accept[field]["parsed_value"], 70, INK, 500)
text(74, 1225, "Amounts agree", 48, "#53654b", 550)
finish("fields.png", "Genuine handwriting / constructed DEV pair / crops magnified")

begin(4, ["Same pixels.", "A different reading."], "#e9e1ef")
crop_plate("numeric-baseline", None, (74, 440, 1126, 770))
for x, label, data in [(74,"BASELINE",base),(670,"WITH ATHN",athn)]:
    text(x, 850, label, 26, MUTED, 650)
    text(x, 910, data["raw_text"], 112, INK, 500)
    h,w = data["model_input_shape"][-2:]
    text(x, 1080, f"{w} × {h} px input", 32, MUTED)
text(74, 1230, f"{athn['preprocessing']['scale']}× recorded preparation scale", 36)
finish("scale.png", "Synthetic DEV input / same frozen model / not an accuracy claim")

begin(6, ["An unreadable field.", "A visible limit."], "#f2eee6")
text(74, 415, "ORIGINAL WRITTEN FIELD", 26, MUTED, 650)
crop_plate("sheet_review", "written", (74, 475, 1126, 800))
text(74, 865, "UNEDITED MODEL READING", 26, MUTED, 650)
text(74, 925, review["written"]["raw_text"], 82, INK, 500)
text(74, 1060, "Parsed value", 32, MUTED)
text(670, 1050, "Not parsed", 49, "#786385", 500)
draw.rounded_rectangle((74, 1180, 1126, 1300), radius=5, fill="#ded3e6")
text(115, 1205, "Needs human review", 51, "#564460", 550)
finish("review.png", "Synthetic DEV input / null stays null / source pixels retained")
(OUT / "provenance.json").write_text(json.dumps({"capture_run":manifest["run_id"], "generator":"scripts/create-gallery-evidence.py", "notice":"Editorial raster compositions of actual saved inputs and outputs; not AI-generated handwriting or new inference.", "panels":[{"file":"fields.png","sources":["sheet_accept"]},{"file":"scale.png","sources":["numeric-baseline","numeric-proposed"]},{"file":"review.png","sources":["sheet_review"]}]}, indent=2))
print("Rendered three 1200 × 1500 evidence plates from saved captures.")

# Supplemental inputs were chosen before inference; include every captured outcome.
supplement = json.loads((OUT / "samples.json").read_text())
provenance = json.loads((OUT / "provenance.json").read_text())
provenance["supplemental_run"] = supplement["run_id"]
for index, study in enumerate(supplement["studies"], 4):
    titles = {"digits": ["Longer strings.", "Visible errors."], "handwriting": ["Small handwriting.", "A changed reading."], "synthetic": ["Another input.", "Another scale."]}
    begin({"digits":1,"handwriting":3,"synthetic":5}[study["id"]], titles[study["id"]], ["#f4e8d8", "#e9e1ef", "#eee5d8"][index-4])
    text(74, 405, "ORIGINAL DEV CROP / " + ("SYNTHETIC" if study["synthetic"] else "GENUINE HANDWRITING"), 25, MUTED, 650)
    value = Image.open(PUBLIC / study["image"].lstrip("/")).convert("RGB")
    draw.rounded_rectangle((74, 460, 1126, 770), radius=5, fill="#fffdf8", outline=LINE, width=2)
    value.thumbnail((940, 230), Image.Resampling.LANCZOS)
    # Enlarge small source fields while retaining their actual pixels.
    ratio = min(940/value.width, 230/value.height)
    value = value.resize((round(value.width*ratio), round(value.height*ratio)), Image.Resampling.LANCZOS)
    image.paste(value, ((1200-value.width)//2, 615-value.height//2))
    for x, mode, label in [(74, "baseline", "BASELINE"), (670, "proposed", "WITH ATHN")]:
        data = study["responses"][mode]["result"]
        text(x, 845, label, 26, MUTED, 650)
        text(x, 915, data["raw_text"], min(100, 720//max(1,len(data["raw_text"]))), INK, 500)
        text(x, 1085, "Parsed value", 28, MUTED)
        text(x, 1135, data["parsed_value"] or "Not parsed", 39, INK, 500)
    text(74, 1250, "Same frozen recogniser. Original output retained.", 31, MUTED)
    finish(study["id"] + ".png", "DEV demonstration / " + ("font-rendered synthetic field" if study["synthetic"] else "genuine handwriting / not a real cheque"))
    provenance["panels"].append({"file": study["id"] + ".png", "sources": [study["source_id"]], "capture": "supplemental"})
(OUT / "provenance.json").write_text(json.dumps(provenance, indent=2))
print("Added three supplemental evidence plates; all six outcomes retained.")
