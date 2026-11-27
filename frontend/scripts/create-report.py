"""Render nine 1200 x 1600 report PNGs from the exact saved API captures.

Creates publication artwork; does not call inference or alter the source images/results.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
OUT = PUBLIC / "field-report"
OUT.mkdir(exist_ok=True)
manifest = json.loads((PUBLIC / json.loads((PUBLIC / "results/latest.json").read_text())["manifest"].lstrip("/")).read_text())
records = {r["id"]: r for r in manifest["records"]}

def result(key):
    return json.loads((PUBLIC / records[key]["response"].lstrip("/")).read_text())

def font(size, weight=450):
    value = ImageFont.truetype(str(PUBLIC / "fonts/Manrope.ttf"), size)
    value.set_variation_by_axes([weight])
    return value

INK, MUTED, PAPER, GREEN, LINE = "#173d31", "#536b5e", "#f6f5eb", "#b7cba8", "#c1ceba"
image, draw = None, None

def text(x, y, value, size=42, fill=INK, weight=450):
    draw.text((x, y), str(value), font=font(size, weight), fill=fill)

def paragraph(x, y, value, width=1020, size=42, fill=MUTED, leading=1.55):
    words, line = value.split(), ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font(size)) > width and line:
            text(x, y, line, size, fill); y += round(size * leading); line = word
        else:
            line = candidate
    if line:
        text(x, y, line, size, fill); y += round(size * leading)
    return y

def start(index, label, title, dark=False):
    global image, draw
    image = Image.new("RGB", (1200, 1600), "#12392e" if dark else PAPER)
    draw = ImageDraw.Draw(image)
    foreground, secondary = ("#edf2e4", "#afc6a7") if dark else (INK, MUTED)
    text(80, 60, "ChequeVerify", 34, foreground, 650)
    text(980, 67, f"{index:02d} / 09", 26, secondary)
    draw.line((80, 127, 1120, 127), fill="#688769" if dark else LINE, width=2)
    text(80, 174, label, 28, secondary, 650)
    for i, line in enumerate(title):
        text(76, 235 + 110 * i, line, 94, foreground, 550)
    return foreground, secondary

def footer(value, dark=False):
    colour = "#afc6a7" if dark else MUTED
    draw.line((80, 1480, 1120, 1480), fill="#688769" if dark else LINE, width=2)
    paragraph(80, 1510, value, size=25, fill=colour, leading=1.3)

def save(index):
    image.save(OUT / f"{index}.png", optimize=True)

def panel(box, fill="#e8eddf", outline=LINE):
    draw.rounded_rectangle(box, radius=8, fill=fill, outline=outline, width=2)

def crop(key, field=None):
    source = Image.open(PUBLIC / records[key]["image"].lstrip("/")).convert("RGB")
    if field:
        source = source.crop(result(key)["rois"][field + "_px"])
    return source

def place(source, box):
    # Scaling here is publication layout only; inference inputs remain byte-identical.
    source = source.copy()
    scale = min((box[2] - box[0]) / source.width, (box[3] - box[1]) / source.height)
    source = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
    x = box[0] + (box[2] - box[0] - source.width) // 2
    y = box[1] + (box[3] - box[1] - source.height) // 2
    image.paste(source, (x, y), source if source.mode == "RGBA" else None)

# Cover: the new solid 3D identity, with generous margins and little copy.
start(1, "THE FIELD REPORT", ["Read beyond", "the handwriting."], True)
place(Image.open(PUBLIC / "brand/mark-3d.png"), (120, 440, 1080, 1320))
text(80, 1340, "Original inputs. Visible reasoning.", 43, "#edf2e4", 500)
footer("Computer Vision / Fall 2026 / Development examples + frozen research", True)
save(1)

# Field evidence is cropped using the pixel ROIs returned by the API.
start(2, "THE INPUT", ["One amount.", "Two ways to write it."])
for field, label, y in [("numeric", "AMOUNT IN FIGURES", 500), ("written", "AMOUNT IN WORDS", 850)]:
    panel((80, y, 1120, y + 300), "#ffffff")
    text(110, y + 28, label, 27, MUTED, 650)
    place(crop("sheet_accept", field), (120, y + 95, 690, y + 265))
    text(770, y + 120, result("sheet_accept")[field]["parsed_value"], 67, INK, 550)
paragraph(80, 1220, "Two genuine handwriting crops, magnified for this constructed demonstration. Each field is read separately, then parsed into a comparable value.", size=39)
footer("Recorded DEV example / Not a real cheque / Source: sheet_accept.json")
save(2)

# Model text is verbatim, including imperfect readings.
baseline = result("numeric-baseline")
start(3, "THE RECOGNISER", ["The image in.", "The raw answer out."])
panel((80, 490, 1120, 790), "#ffffff")
text(110, 520, "ORIGINAL SYNTHETIC NUMERIC CROP", 27, MUTED, 650)
place(crop("numeric-baseline"), (200, 605, 1000, 735))
text(80, 870, "BASELINE / RAW MODEL TEXT", 29, MUTED, 650)
text(75, 930, baseline["raw_text"], 185, INK, 550)
text(80, 1170, f"Parsed value   {baseline['parsed_value']}", 49, INK, 550)
paragraph(80, 1280, "LoGo-HTR uses the released checkpoint on CPU. The displayed answer is the model's original output, with no manual correction.", size=39)
footer("Recorded DEV output / Request " + baseline["request_id"])
save(3)

# A same-input comparison; no reconstructed OCR or invented performance.
athn = result("numeric-proposed")
start(4, "ADAPTIVE TEXT-HEIGHT NORMALISATION", ["Same recogniser.", "A different scale."])
text(80, 500, "ONE INPUT / TWO PREPARATION PATHS", 29, MUTED, 650)
for x, label, response in [(80, "BASELINE", baseline), (630, "ATHN", athn)]:
    panel((x, 575, x + 490, 1030), "#e6ebdd")
    text(x + 30, 605, label, 28, MUTED, 650)
    place(crop("numeric-baseline"), (x + 35, 690, x + 455, 825))
    text(x + 25, 865, response["raw_text"], 101, INK, 550)
text(80, 1110, "Input height", 34, MUTED)
text(80, 1160, f"{athn['preprocessing']['input_hw'][0]} px", 77, INK, 550)
text(575, 1110, "Prepared height", 34, MUTED)
text(575, 1160, f"{athn['preprocessing']['output_hw'][0]} px", 77, INK, 550)
paragraph(80, 1295, "ATHN adjusts text scale before recognition. This recorded synthetic DEV example illustrates the change; one example is not evidence of overall accuracy.", size=36)
footer("Actual outputs / Configuration selected on DEV, frozen before test evaluation")
save(4)

# All three actual constructed demo decisions and their raw parsed values.
start(5, "THE DECISION", ["Agreement, difference,", "or a closer review."])
for index, (key, title) in enumerate([("sheet_accept", "Amounts agree"), ("sheet_flag", "Amounts differ"), ("sheet_review", "Human review")]):
    response = result(key)
    y = 500 + index * 275
    panel((80, y, 1120, y + 245), ["#e2ecd9", "#f0e5cf", "#e2e5e6"][index])
    text(110, y + 28, title, 49, INK, 600)
    text(110, y + 110, response["numeric"]["parsed_value"] or "Not parsed", 43)
    text(590, y + 110, response["written"]["parsed_value"] or "Not parsed", 43)
    text(110, y + 180, f"FIGURES / WORDS     Request {response['request_id']}", 25, MUTED)
paragraph(80, 1345, "Agreement compares recognised values. It does not establish authenticity.", size=35)
footer("Three constructed DEV examples / Source responses retained unchanged")
save(5)

# Actual frozen metrics, separated by dataset type and retaining raw rates.
benchmark = result("benchmark")
genuine = benchmark["datasets"]["D1_gnhk_words_genuine"]
synthetic = benchmark["datasets"]["D6_syn_numeric_SYNTHETIC"]
start(6, "THE EVIDENCE", ["Read the results.", "Keep their context."])
text(80, 500, f"GENUINE HANDWRITING / {genuine['n_eligible']} GNHK WORDS", 29, MUTED, 650)
text(80, 555, "Character error rate / lower is better", 36)
for i, (key, label, colour) in enumerate([("baseline", "Baseline", "#b4c5ad"), ("proposed", "ATHN", "#416d52")]):
    y = 650 + i * 105
    text(80, y, label, 34)
    draw.rounded_rectangle((300, y + 8, 300 + round(genuine["cer"][key] / .35 * 600), y + 64), radius=4, fill=colour)
    text(940, y, genuine["cer"][key], 43)
paragraph(80, 900, "The overall genuine-handwriting change was not statistically significant. A lower rate on this subset does not establish a general improvement.", size=38)
draw.line((80, 1100, 1120, 1100), fill=LINE, width=2)
text(80, 1140, "SYNTHETIC NUMBERS / EXACT PARSED VALUES", 29, MUTED, 650)
text(80, 1200, f"{synthetic['value_exact']['baseline']} / {synthetic['n_eligible']}", 87, MUTED, 500)
text(620, 1200, f"{synthetic['value_exact']['proposed']} / {synthetic['n_eligible']}", 87, INK, 550)
text(80, 1320, "BASELINE", 26, MUTED, 650)
text(620, 1320, "ATHN", 26, MUTED, 650)
paragraph(80, 1390, "Every synthetic pair went to review under both methods.", size=31)
footer("Saved locked-test metrics / Source: COMPARATIVE_METRICS.json / No new evaluation")
save(6)

# Three additional editorial pages. Existing quantitative pages are preserved.
review = result("sheet_review")
start(7, "WHEN A READING NEEDS REVIEW", ["A visible failure.", "An honest outcome."])
panel((80, 490, 1120, 810), "#ffffff")
text(110, 520, "ORIGINAL SYNTHETIC WRITTEN FIELD", 27, MUTED, 650)
place(crop("sheet_review", "written"), (130, 600, 1070, 755))
text(80, 865, "RAW MODEL TEXT", 27, MUTED, 650)
text(76, 920, review["written"]["raw_text"], 82, INK, 550)
for x, label, value, fill in [(80, "PARSED VALUE", "Not parsed", "#e7e8df"), (630, "DECISION", "Human review", "#e2e9df")]:
    panel((x, 1085, x + 490, 1280), fill)
    text(x + 28, 1115, label, 25, MUTED, 650)
    text(x + 28, 1170, value, 51, INK, 600)
paragraph(80, 1335, "An unparseable reading stays visible. The system leaves the value empty and requests human review.", size=33)
footer("Recorded DEV failure / Request " + review["request_id"])
save(7)

start(8, "TWO DIFFERENT DOMAINS", ["Handwritten evidence.", "Synthetic examples."], True)
for x, label, key, field in [(80, "GENUINE HANDWRITING", "sheet_flag", "numeric"), (630, "SYNTHETIC FIELD", "numeric-proposed", None)]:
    panel((x, 500, x + 490, 855), "#f7f6ec", "#6d8a6b")
    text(x + 25, 530, label, 24, MUTED, 650)
    place(crop(key, field), (x + 35, 635, x + 455, 795))
text(80, 930, "ELIGIBLE CROPS / SAVED LOCKED TEST", 28, "#b7cba8", 650)
rows = [("GNHK words", "D1_gnhk_words_genuine"), ("CVL digits", "D4_cvl_numeric_genuine"), ("Synthetic numeric", "D6_syn_numeric_SYNTHETIC"), ("Synthetic written", "D6_syn_words_SYNTHETIC")]
for i, (label, key) in enumerate(rows):
    y = 1000 + i * 83
    count = benchmark["datasets"][key]["n_eligible"]
    text(80, y, label, 34, "#edf2e4")
    draw.rounded_rectangle((510, y + 8, 510 + count / 210 * 440, y + 46), radius=4, fill="#a0b99a" if "SYNTHETIC" not in key else "#9e8fbd")
    text(1000, y - 3, count, 43, "#edf2e4", 550)
paragraph(80, 1385, "Reported separately. Synthetic gains are not evidence of performance on real handwritten cheques.", size=31, fill="#b7cba8")
footer("Actual DEV input crops above / Historical dataset counts below", True)
save(8)

start(9, "THE SYSTEM, IN VIEW", ["From pixels", "to a decision."], True)
place(Image.open(OUT / "scan-concept.png"), (50, 460, 1150, 1180))
text(80, 1190, "Concept illustration / not model output", 26, "#b7cba8")
for i, label in enumerate(["Browser", "API", "LoGo-HTR", "Review"]):
    x = 80 + i * 270
    panel((x, 1270, x + 230, 1385), "#e4ebdc", "#6e8b6d")
    text(x + 22, 1302, label, 33, INK, 600)
    if i < 3: text(x + 238, 1300, "→", 33, "#b7cba8")
footer("An inspectable research workflow / Original inputs, unchanged readings, human judgement", True)
save(9)

# Editable SVG companions expose the same explanatory graphics independently.
from html import escape
svg_head = '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560"><rect width="1200" height="560" rx="16" fill="#f6f5eb"/><g font-family="Arial,sans-serif" fill="#173d31">'
review_svg = svg_head + '<text x="60" y="80" font-size="30">Recorded written-field failure</text>'
for x, label, value in [(60, 'Raw text', review['written']['raw_text']), (450, 'Parsed value', 'null'), (840, 'Outcome', 'Human review')]:
    review_svg += f'<rect x="{x}" y="155" width="300" height="230" rx="12" fill="#e3eadd" stroke="#a5b99c"/><text x="{x+25}" y="208" font-size="22">{label}</text><text x="{x+25}" y="287" font-size="31">{escape(value)}</text>'
review_svg += '<path d="M375 265H430M765 265H820" stroke="#72579c" stroke-width="3"/><text x="60" y="475" font-size="22">Unparseable model text routes to human review; no value is invented.</text></g></svg>'
(OUT / 'review-path.svg').write_text(review_svg, encoding='utf-8')
domain_svg = svg_head + '<text x="60" y="80" font-size="30">Separate domains. Original eligible counts.</text>'
for i, (label, key) in enumerate(rows):
    y = 155 + i * 85
    count = benchmark['datasets'][key]['n_eligible']
    colour = '#416d52' if 'SYNTHETIC' not in key else '#8f7ba8'
    domain_svg += f'<text x="60" y="{y+25}" font-size="24">{label}</text><rect x="430" y="{y}" width="{count/210*560}" height="34" rx="4" fill="{colour}"/><text x="1040" y="{y+26}" font-size="27">{count}</text>'
(OUT / 'domain-map.svg').write_text(domain_svg + '</g></svg>', encoding='utf-8')
system_svg = svg_head + '<text x="60" y="80" font-size="30">Explanatory system flow</text>'
for i, (title, detail) in enumerate([('Browser','Original input'),('FastAPI','Explicit request'),('LoGo-HTR','Frozen checkpoint'),('Review','Visible evidence')]):
    x = 45 + i * 295
    system_svg += f'<rect x="{x}" y="170" width="225" height="200" rx="12" fill="#e3eadd" stroke="#a5b99c"/><text x="{x+20}" y="240" font-size="30">{title}</text><text x="{x+20}" y="290" font-size="20">{detail}</text>'
    if i < 3: system_svg += f'<path d="M{x+235} 267H{x+280}" stroke="#72579c" stroke-width="3"/>'
(OUT / 'system-flow.svg').write_text(system_svg + '</g></svg>', encoding='utf-8')

(OUT / "provenance.json").write_text(json.dumps({
    "source_run": manifest["run_id"], "dimensions": [1200, 1600],
    "pages": 9, "source_responses": ["sheet_accept", "sheet_flag", "sheet_review", "numeric-baseline", "numeric-proposed", "benchmark"],
    "notice": "Publication layout from recorded DEV examples and saved frozen metrics. No inference or metric recomputation.",
}, indent=2) + "\n")
notes = [
    {"title": "Read beyond the handwriting.", "text": "ChequeVerify reads handwritten amounts in figures and words, compares their parsed values, and keeps the original evidence visible. This report contains recorded development examples and saved research results."},
    {"title": "One amount. Two ways to write it.", "text": "The agreement example contains two genuine handwriting crops in a constructed DEV sheet. The raw numeric reading is 1 and the written reading is one. Both parse to 1.00. Input crops are magnified for publication; this is not a real cheque."},
    {"title": "The image in. The raw answer out.", "text": f"LoGo-HTR uses its released frozen checkpoint on CPU. On this synthetic numeric DEV input, baseline returns the unedited raw text {baseline['raw_text']}, parsed as {baseline['parsed_value']}. Request {baseline['request_id']}."},
    {"title": "Same recogniser. A different scale.", "text": f"The same synthetic DEV input produces {baseline['raw_text']} under baseline and {athn['raw_text']} under ATHN. Input height is {athn['preprocessing']['input_hw'][0]} pixels; prepared height is {athn['preprocessing']['output_hw'][0]} pixels. ATHN is a training-free preprocessing step selected on DEV and frozen before test evaluation. This example is not an overall accuracy claim."},
    {"title": "Agreement, difference, or a closer review.", "text": "Three recorded DEV examples: 1.00 and 1.00 agree; 25000.00 and 1.00 differ; 3003.00 and an unparseable written reading need human review. Agreement compares recognised values; it does not establish authenticity."},
    {"title": "Read the results. Keep their context.", "text": f"Saved locked-test results: on {genuine['n_eligible']} GNHK word crops, CER is {genuine['cer']['baseline']} baseline and {genuine['cer']['proposed']} ATHN. The overall genuine-handwriting change was not statistically significant. Synthetic numeric exact parsed values are {synthetic['value_exact']['baseline']}/{synthetic['n_eligible']} baseline and {synthetic['value_exact']['proposed']}/{synthetic['n_eligible']} ATHN. Every synthetic pair went to review under both methods. No new evaluation was run."},
]
notes += [
    {"title": "A visible failure. An honest outcome.", "text": f"The recorded synthetic written field returns raw text {review['written']['raw_text']}, a null parsed value, and human review. No numeric value is fabricated for an unparseable reading.", "diagram": "/field-report/review-path.svg"},
    {"title": "Handwritten evidence. Synthetic examples.", "text": "Genuine and synthetic inputs are shown separately. The saved test includes 160 GNHK word crops, 210 CVL digit strings, 77 eligible synthetic numeric fields and 87 eligible synthetic written fields. The original source images above are recorded DEV examples, not test inference.", "diagram": "/field-report/domain-map.svg"},
    {"title": "From pixels to a decision.", "text": "A conceptual illustration accompanies the explanatory browser, API, frozen recogniser and human-review workflow. The artwork is not inference output. Original inputs, model text and captured metadata remain inspectable.", "diagram": "/field-report/system-flow.svg"},
]
for note in notes:
    note.setdefault("diagram", None)

generated = ROOT / "src/generated"
generated.mkdir(exist_ok=True)
(generated / "report.ts").write_text("// Generated by scripts/create-report.py from the recorded capture.\nexport const reportNotes = " + json.dumps(notes, indent=2) + ";\n", encoding="utf-8")
print("Rendered nine 1200 x 1600 PNG pages from capture", manifest["run_id"])
