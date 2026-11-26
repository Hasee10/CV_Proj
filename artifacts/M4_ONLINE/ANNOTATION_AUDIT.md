# M4-ONLINE: annotation audit

No label was produced by LoGo-HTR or by the parsers under evaluation. "AI-checked" below means Claude viewed the images. It is **not** human verification, and no sample is marked human-verified.

| Set | Label source | Checks performed | Findings |
|---|---|---|---|
| D4 CVL | filename class label (CVL readme: "numbers before the first minus are the class labels") | MD5 of the archive matches Zenodo; crops byte-identical to the zip members (test); 20 crops viewed (contact sheet A) | all 20 viewed crops agree with their labels. The writer id is **inferred** from the second filename field: 121 of 127 ids hold exactly one copy of each of the 10 strings, while the readme calls it a "unique ID" |
| D5 GNHK pairs | GNHK `text` annotations (published) | all 54 pairs viewed (contact sheet B); page split identical to the frozen D1 subset (asserted) | labels used as published. Possible noise: several `1` crops are bare vertical strokes; one `80` could be read as `82`; some integer crops are only a few pixels tall; `TEn` keeps the annotator's casing. Not relabelled |
| D6 synthetic | HF annotations `amt_in_figures` / `amt_in_words` | **all 130 cheques viewed** with their annotations; words values resolved by an independent verbaliser lookup (124/124 non-blank words annotations; 6 words and 18 numeric fields are blank); the frozen `words_value` parser agrees on all 124 (cross-check only, not the GT source) | annotations match the rendered text in every case viewed. **14 natural mismatches** (numeric and words differ in the source, e.g. `4092` vs "Three Thousand Seven Hundred and Twelve") were confirmed as rendered. 24 blank fields (both directions) were confirmed blank |

## Crop quality (D6, all 260 checked visually after 4 box refinements)
- No handwriting is clipped in the final boxes. Earlier versions clipped HSBC second lines, Canara long words, and AXIS/ICICI digit tops and bottoms; these were fixed before freezing.
- Residual printed content is kept rather than clipping text:
  - ICICI words: a small fragment of the printed "रुपये" label at the left edge;
  - HSBC words: a "RE" fragment of the "SINGAPORE DOLLARS" label;
  - ICICI, AXIS and Canara numerals: some printed box or underline segments;
  - Canara and ICICI words: occasional descenders from the payee line above;
  - one HSBC numeral: a small signature arc.
- These are identical for baseline and improved systems.

## Duplicate review
227 cross-split candidates (11 exact, 216 near) were all synthetic. They were resolved by the documented rule in `scripts/review_duplicates.py`:
- 14 `blank_field` (both crops verified blank);
- 213 `not_duplicate` (different ground truth).

Every entry is marked "rule (automated, not human)".
