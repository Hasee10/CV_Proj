"""Generate original vector artwork for the local LeafThrough project booklet."""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[1] / 'public' / 'field-notes'
OUT.mkdir(parents=True, exist_ok=True)
pages = [
    ('FIELD NOTES', ['A closer', 'look.'], ['Handwriting. Recognition.', 'Human judgement.'], 'A project companion / Fall 2026'),
    ('THE QUESTION', ['One cheque.', 'Two expressions.'], ['The amount in figures.', 'The amount in English words.', '', 'Select both fields. Read their values.', 'Compare what the model recognises.'], 'Field selection is manual. No automatic detection.'),
    ('THE BASELINE', ['The original', 'recogniser.'], ['LoGo-HTR / released checkpoint.', 'CPU inference. Unchanged weights.', '', 'The baseline keeps the upstream', 'transform and decoding pipeline.'], 'Mitra, Mondal & Jawahar / WACV 2026'),
    ('THE PROPOSED METHOD', ['A question', 'of scale.'], ['ATHN / adaptive text-height normalisation.', 'A training-free preprocessing step.', '', 'Selected on the development split.', 'Frozen before locked-test evaluation.'], 'Same recogniser. Different preparation.'),
    ('THE COMPARISON', ['Agreement', 'needs context.'], ['AMOUNTS AGREE / both parse and match', 'AMOUNTS DIFFER / both parse and differ', 'HUMAN REVIEW / either does not parse', '', 'Recognised values are compared strictly.', 'Agreement is not proof of authenticity.'], 'Every result needs human interpretation.'),
    ('THE EVIDENCE', ['Evidence before', 'certainty.'], ['Genuine handwriting and synthetic data', 'are reported separately.', '', 'Every synthetic pair went to review.', 'The genuine-handwriting change was', 'not statistically significant.'], 'Read the results alongside their limitations.'),
]
for index,(kicker,title,body,footer) in enumerate(pages):
    dark = index in (0,5)
    bg,fg,muted,accent = ('#132b2a','#efeee4','#aabcb0','#b9c9a7') if dark else ('#eeeee4','#163330','#526b60','#577866')
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1240" viewBox="0 0 900 1240"><rect width="900" height="1240" fill="{bg}"/>',f'<g font-family="Arial, sans-serif" fill="{fg}">',f'<text x="66" y="88" font-size="23" letter-spacing="-1">ChequeVerify.</text><text x="834" y="88" text-anchor="end" font-family="monospace" font-size="15">{index+1:02d} / 06</text>',f'<path d="M66 116H834" stroke="{muted}" stroke-width="1"/>',f'<text x="66" y="183" font-family="monospace" font-size="16" letter-spacing="3" fill="{muted}">{kicker}</text>']
    for line_no,line in enumerate(title):
        parts.append(f'<text x="60" y="{292+line_no*96}" font-size="86" letter-spacing="-5">{escape(line)}</text>')
    if index==0:
        parts.append(f'<g fill="none" stroke="{accent}" opacity=".7" transform="translate(450 710) rotate(-22)">')
        for r in range(50,240,13):
            parts.append(f'<ellipse rx="{r}" ry="{r*.7}" stroke-width="1.5"/>')
        parts.append(f'<path d="M-280 0H280M0-230V230" opacity=".4"/></g>')
        y=1025
    else:
        parts.append(f'<g stroke="{accent}" fill="none" stroke-width="2" opacity=".7"><rect x="66" y="454" width="768" height="190"/><path d="M96 510H620M96 556H550M96 600H740"/><rect x="640" y="550" width="160" height="60"/></g>')
        y=735
    for line_no,line in enumerate(body):
        parts.append(f'<text x="66" y="{y+line_no*44}" font-size="25" fill="{muted}">{escape(line)}</text>')
    parts.append(f'<path d="M66 1130H834" stroke="{muted}"/><text x="66" y="1178" font-size="17" fill="{muted}">{escape(footer)}</text></g></svg>')
    (OUT / f'{index+1}.svg').write_text(''.join(parts),encoding='utf-8')
print('Created six original field-note pages.')
