# M6 experiment protocol (frozen 2026-11-26, before any M6 inference)

Starting commit `e225ee8`. Checkpoint `25db3a51…c432`. Frozen M4-FINAL manifests (hashes verified at run time). **Development split only.** The baseline configuration is unchanged: upstream preprocessing, beam 10, `SSL_HWD_Dict.txt`, CPU, batch 1. Seed `20261126` everywhere. No test-split inference, no training.

## Population
- **Clean analysis:** the 245 recognition-eligible dev entries, using the M5-DEV predictions (reused, not re-run).
- **Stress:** the same 245 entries × 5 corruptions × 3 levels = **3,675 variants**, made with `scripts/stress_corrupt.py`. The parameters, seeds and naming are those frozen in `artifacts/M4/STRESS_TEST_PROTOCOL.md`. Every variant keeps `parent_id`, `parent_sha256` and the parent's split.
  - **Runtime pilot (fixed rule):** all 15 variants of the first 2 eligible dev entries per dataset (D1, D4, D5, D6) by sorted id, 120 variants.
  - **Fallback if the full matrix exceeds about 3 h of estimated CPU time:** drop severity level 2 for every entry (2,450 variants). This rule is set now and does not depend on predictions.

## Clean-analysis features and fixed bins
- **Input size:** effective input size after the upstream transform (height × width), from M5 `input_shape`. Height bins: `<32`, `32–63`, `64–127`, `≥128` px.
- **Foreground (ink):** Otsu binarisation of the greyscale crop. Ink height is the 5th–95th percentile span of ink rows, scaled to the transformed size. Ink-height bins: `<12`, `12–23`, `24–47`, `≥48` px. Occupancy is the ink pixel fraction.
- **Contrast and blur:** contrast = grey p95 − p5 and grey standard deviation; blur = variance of the Laplacian.
- **Text features:** GT length bins `1–3`, `4–7`, `≥8` characters; word count (`single` / `multi`, i.e. a space in GT); `repeated_zero` (GT contains `00`); `repeated_other_digit` (adjacent identical non-zero digits); `has_digit`; `has_punct` (any of `, . - / : ( )`); `genuine` vs `synthetic`.
- Every subgroup reports n. Groups with n < 10 are labelled **inconclusive**. Wherever a factor is confounded with the dataset (for example synthetic text size together with synthetic fonts), the confound is stated.

## Robustness metrics
For each dataset × corruption × level: n, exact, aggregate CER, WER, punctuation P/R, amount-value exact, failures, and median/P95 latency.

Paired comparisons against the clean M5 prediction of the same parent:
- ΔCER and Δexact (percentage points);
- correct→incorrect and incorrect→correct transitions;
- amount-value changes.

95% confidence intervals use a **cluster bootstrap** (1,000 resamples, seed 20261126) over source groups:
- D1: page;
- D4: inferred writer;
- D6: cheque;
- D5 is too small for an interval.

Aggregate severity trends are reported as observed. Strict per-image dose-response is **not** claimed, because the illumination direction and noise seed differ by level.

## Diagnostics (dev only; IDs, subsets and conditions fixed now)
Subsets use sorted ids among eligible dev entries. Images are made by `scripts/m6_prepare.py`. Recognition only ever receives images.

| ID | Question | Subset | Conditions |
|---|---|---|---|
| DX-A | Is the pipeline sane? | all 245 eligible dev entries | channel order, pixel range, polarity (background vs ink brightness), transformed dimensions, token-id range, decoder hyper-parameters |
| DX-B | Does resolution matter? | first 8 each of D1, D4, D6 numeric, D6 words (32 entries) | original (M5) · 2× · 4× isotropic upscale (`cv2.INTER_CUBIC`) before the upstream transform; effective dimensions recorded after the upstream caps (h ≤ 256, w ≤ 1024) |
| DX-C | Does word segmentation matter? | first 8 D6 words entries | full line 1× (M5) · full line 2× (from DX-B or computed) · segmented 1× · segmented 2×. Segmentation: binarise, remove long horizontal lines (as DX-D), split text lines on empty rows, then split words on column gaps ≥ 0.5 × median ink height. **Oracle-validated:** GT word count is used only to report whether the geometry matched, never as model input. Word predictions are joined with spaces for scoring |
| DX-D | Do printed lines and borders hurt? | first 8 D6 numeric and first 8 D6 words entries from templates with box lines or underlines (AXIS, Canara, ICICI) | original 1× and 2× · line-removed 1× and 2×. Line removal: Otsu, then morphological opening with a horizontal kernel ≥ 40% of crop width and a vertical kernel ≥ 70% of crop height; those pixels are set to the background median. Removed-pixel counts are recorded; handwriting pixels lying on a line can be lost, and this is reported |
| DX-E | Punctuation and repeated digits | all clean dev predictions plus stress variants | counts of zero insertions and deletions, digit substitutions, missing commas and decimals, punctuation substitutions; financial ratio pred/GT value where both parse |

Diagnostic metrics: exact, CER, amount-value exact and parseable count, and the effective input height. These are **exploratory interventions**, not the M7 method.

## Amount-pair failure reasons (dev pairs)
Each pair is assigned exactly one reason, in this order:
1. `blank_source_field` (GT unresolved);
2. `both_unparseable`;
3. `numeric_unparseable`;
4. `written_unparseable`;
5. `parsed_but_wrong_value`;
6. `correct`.

Stress pairs use both fields' variants at the same corruption and level.

## Outputs
`artifacts/M6/` holds JSON results, reports and figures. Generated images go to `data/stress/` and `data/diagnostics/` (git-ignored, regenerable). Predictions are cached by image hash plus the full inference configuration.

## Amendment A1 (before any DX-C inference; based only on segmentation geometry)
The frozen DX-C rule produced the GT word count for 1 of 8 lines. Dotted printed underlines survive the horizontal-line opening and join all columns, giving single-segment lines. Change: before band and gap detection, rows whose ink covers more than 35% of the width are removed. GT word counts are still used only to report the geometric match. No recognition output had been produced or seen.

## Amendment A2 (before any DX-C inference; geometry only; final)
A1 over-segmented: thin font rows exceeded 35% coverage, giving 6-107 segments. A1 is withdrawn. Column gaps are now measured only within the central text zone of each band (the 25th-75th percentile of ink-row positions), which excludes underlines and ascenders. If a line still does not match its GT word count, its word boxes come from **AI visual review of the image** (an oracle; recorded per line). No further geometric tuning will be done.
