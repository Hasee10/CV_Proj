# M6 diagnostic report (exploratory interventions, dev only)

All subsets and conditions were frozen in `EXPERIMENT_PROTOCOL.md`. Amendments A1 and A2 changed only the DX-C segmentation geometry, before any DX-C recognition. Raw predictions are in `DIAGNOSTIC_RAW.json` (302 entries, 284 unique images, 0 errors) and aggregates in `DIAGNOSTIC_RESULTS.json`. **These are diagnostics, not the M7 method.**

## DX-A: pipeline sanity
- All 245 dev inputs are dark ink on a light background, uint8 RGB.
- Upstream `ToTensor` scales pixels to [0, 1], and PIL `convert('RGB')` fixes the channel order.
- 245/245 effective sizes match `ScaleToLimitRange(16–1024 w, 16–256 h)`.
- Token ids fall in 9–90, inside the 97-token vocabulary.
- Beam 10, max_len 200, alpha 1.0.

No pipeline fault was found.

## DX-B: isotropic upscaling before the upstream transform (`INTER_CUBIC`)
| Subset (n = 8) | Original: median effective height → exact / CER | 2× | 4× |
|---|---|---|---|
| D1 GNHK | 80 px → 4 / 0.229 | 160 px → 3 / 0.314 | 256 px (capped) → 3 / 0.371 |
| D4 CVL | 72 px → 4 / 0.146 | 143 px → 1 / 0.250 | 230 px → **0 / 0.896** |
| D6 numeric (synthetic) | 34 px → 0 / 0.906 | 67 px → 1 / 0.500 | 134 px → **5 / 0.406** (value exact 5/8) |
| D6 words (synthetic) | 32 px → 0 / 0.868 | 64 px → 0 / 0.799 | 119 px → 0 / 0.734 |

Upscaling helps only inputs that start small, and it clearly harms genuine crops that already sit at about 70–80 px. The 4× synthetic words are capped by the 1024-px width limit, so their effective scale is below 4×. Upscaling does not reconstruct lost detail; it changes the scale the model sees.

## DX-C: multiword lines (first 8 synthetic words dev lines)
| Condition | Exact lines | CER | WER |
|---|---|---|---|
| full line 1× (baseline) | 0 | 0.868 | 1.00 |
| full line 2× | 0 | 0.799 | 1.00 |
| automatic geometric segments 1× | 0 | 0.796 | 1.24 |
| automatic geometric segments 2× | 0 | 0.582 | 1.16 |
| oracle word crops 1× | 0 | 0.770 | 1.00 |
| **oracle word crops 2×** | 0 | **0.457** | **0.84** |

- Per-word exact: 0/49 at oracle 1×, **8/49 at oracle 2×**.
- The automatic geometric segmentation matched the word count on **0/8** lines, even after the two geometry amendments.
- The oracle boxes are AI visual-review regions, not an algorithm.
- Example (oracle 2×): GT "One Thousand Seven Hundred and Thirty Seven" → `one Trowand soven Himades and mmy soven`.

## DX-D: removing printed lines and borders (AXIS, Canara and ICICI templates)
| Field (n = 8) | Original 1× | Original 2× | Lines removed 1× | Lines removed 2× |
|---|---|---|---|---|
| numeric CER (parseable) | 1.000 (0) | **0.688 (5)** | 1.031 (0) | 0.906 (4) |
| words CER | 0.854 | 0.796 | 0.854 | 0.803 |

Line removal (median 183 px removed from numbers, 684 from words) gives no benefit and slightly hurts at 2×. Strokes that touch lines are probably removed too. Foreground isolation by line removal is **not** a promising direction on this evidence.

## DX-E: digits and punctuation
- **Clean dev (147 digit-bearing samples):**
  - 75 digit substitutions, 1 zero deletion, 0 zero insertions;
  - 5 comma and 2 decimal errors, 2 punctuation substitutions;
  - of 96 predictions where both values parse, 45 are exact, 10 are off by ≥ ×10, and 29 are within 10% but wrong.
- **Stress, per corruption family** (441 digit-bearing variants each): 213–235 digit substitutions, 1–7 zero insertions, 0–4 zero deletions, 26–33 values off by ≥ ×10.
- Repeated-zero errors are rare on these data. Digit substitutions and order-of-magnitude value errors are the main financial risk.
