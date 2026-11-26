# ChequeVerify evaluation data: dataset card (M4-ONLINE, supersedes the D2 custom design)

| Set | Genuine? | Samples | Pairs | Split (dev / test) | Grouping | Licence | Manifest |
|---|---|---|---|---|---|---|---|
| D1 GNHK subset | genuine | 240 words | - | 80 / 160 | page | CC-BY-4.0 | `data/public/gnhk/subset/manifest.json` |
| D4 CVL numeric | genuine | 300 numeric strings | - | 90 / 210 | inferred writer (30) | CC-BY-NC-4.0 | `data/benchmarks/cvl_numeric/manifest.json` |
| D5 GNHK number pairs | genuine | 72 (27 words, 45 integers) | 54 (27 match / 27 mismatch, all constructed) | 3 / 69 crops; 2 / 52 pairs | page | CC-BY-4.0 | `data/benchmarks/gnhk_pairs/manifest.json` |
| D6 synthetic cheques | **synthetic** | 260 (130 num, 130 words) | 236 | 78 / 182 crops; 72 / 164 pairs | cheque | Apache-2.0 (declared) | `data/benchmarks/syn_cheques/manifest.json` |
| D0 M3-B | genuine | 9 (21 condition entries) | - | exploratory only | 1 writer | student's own | `artifacts/M3_B_final/` |

Pairs are in `data/benchmarks/amount_pairs.json`:
- **D5:** 27 match and 27 mismatch, all `constructed_cross_page`.
- **D6:** 92 match, 14 mismatch and 24 unresolved `natural_same_cheque` pairs, plus 106 mismatch `constructed_cross_cheque` pairs.

## Fields
`id`, `file`, `sha256`, `ground_truth` (dataset annotation), `gt_value` (independent value), `label_status`, `category`, `genuine_handwriting`, `writer_id` (CVL inferred; else null), `group_id`, `split`, `crop_type`, plus provenance fields:
- D4: `source_entry` (zip member);
- D6: `source_file` and `source_sha256`;
- D5 and D6: `crop_box_xyxy`.

## Crop types
- **D4 `dataset_provided_image`:** byte-identical CVL PNGs (already single strings).
- **D5 `annotation_polygon_bbox`:** the axis-aligned box of the official GNHK polygon on the EXIF-transposed page, the same method as D1. Three D5 crops are byte-identical to D1 samples, in the same split.
- **D6 `template_oracle_box`:** one fixed box per template and field, set from per-template ink-variance heatmaps and checked on every one of the 130 cheques. These are oracle crops for a **known template**, not automatic field detection.

## Values (independent of the evaluated parsers)
- D4: `int(digit string)`.
- D5: an explicit number-word table (`one`→1 …).
- D6:
  - numeric: `int(amt_in_figures)`;
  - words: lookup of the normalised annotation in an independent integer→English verbaliser table (1..99,999). All 124 non-blank words annotations resolved; 6 words and 18 numeric fields are blank.

## Privacy
D6 crops contain only the two amount fields: no payee, account number, MICR line, signature or bank logo. The full synthetic cheque images stay in a git-ignored cache. CVL and GNHK carry no personal identifiers beyond handwriting.
