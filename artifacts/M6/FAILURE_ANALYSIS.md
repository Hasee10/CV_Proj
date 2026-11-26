# M6 failure analysis (dev split only; frozen baseline)

Sources:
- `CLEAN_FAILURE_ANALYSIS.json`: 245 clean dev samples with per-sample features.
- `STRESS_METRICS.json`: 3,675 paired variants.
- `DIAGNOSTIC_RESULTS.json`.
- `AMOUNT_FAILURE_ANALYSIS.json`.

Figures are in `figures/`. Every number here was measured on dev; no test data was used.

## 1. Clean baseline: where it fails
- **Genuine vs synthetic:**
  - genuine: 74/173 exact, aggregate CER 0.233;
  - synthetic: 0/72, CER 0.882.
- **Input height after the upstream transform:**

  | Height | n | Exact | CER |
  |---|---|---|---|
  | < 32 px | 43 | 3 | 0.892 |
  | 32–63 px | 92 | 32 | 0.651 |
  | 64–127 px | 79 | 31 | 0.216 |
  | ≥ 128 px (all D1) | 31 | 8 | 0.416 |

  - The < 32 px group is mostly synthetic (39 of 43), so height and font domain are confounded.
  - **Within D1**, the large crops (≥ 128 px) are worse (CER 0.416, n = 31) than 32–127 px crops (0.22). Within each synthetic group, CER is about 0.86–1.04 in every height bin.
- **Length and word count:**
  - single tokens: 74/208 exact, CER 0.330;
  - multiword lines: 0/37, CER 0.871. All 37 are synthetic, so word count is fully confounded with the synthetic domain.
- **Digits and repeats:**
  - repeated zeros: 7/12 exact, CER 0.104 (mostly CVL `25000`), so they are *not* a weak spot on dev;
  - digit-bearing samples: 75 digit substitutions;
  - 10 of 96 value-parsed predictions are off by ×10 or more.
- **Punctuation:** 17 samples contain punctuation (2 exact). There are 5 comma errors and 2 decimal errors. The punctuation sample is too small to be conclusive.

## 2. Controlled corruptions (paired, same parents; 95% cluster-bootstrap CI)
- **Mild levels (s1)** change little: |ΔCER| ≤ 0.06 on genuine sets, and most CIs include 0.
- **Severe levels** (CI excludes 0 unless stated):

  | Set | Corruption at s3 | ΔCER [95% CI] | Δexact |
  |---|---|---|---|
  | D4 CVL | contrast | +0.290 [0.12, 0.46] | −16.7 pp |
  | D4 CVL | illumination | +0.032 [0.018, 0.048] | −11.1 pp |
  | D4 CVL | blur | +0.068 [0.013, 0.133] | −7.8 pp |
  | D1 GNHK | contrast | +0.422 [0.08, 1.04] | −6.2 pp |
  | D1 GNHK | noise | +0.135 [0.05, 0.21] | −7.5 pp |
  | D1 GNHK | low resolution | +0.064 [0.01, 0.13] | −5.0 pp |
  | D1 GNHK | blur | +0.719 [0.09, 2.03] | −1.2 pp |

  - The D1 blur result is driven by a few very long garbage outputs.
- **Trends are not strictly monotonic.** For example, D1 blur s2 gained 5 points of exact match, and D4 noise s3 is milder than s2 for exact match. Aggregate trends only; no per-image dose-response is claimed.
- **Synthetic sets:** all stay at 0 exact under every corruption.
  - D6 words: low resolution and blur add +0.03 to +0.07 CER (CIs exclude 0), while contrast slightly lowers CER (−0.02).
  - The synthetic baseline is already at the floor, so corruption effects there are hard to interpret.
- **Legibility (AI visual check, not human):** at s3, the synthetic numbers and words become illegible under low resolution and blur, while CVL digits stay legible under all corruptions. Some severe synthetic degradation therefore reflects information loss, not model weakness.

## 3. Hypotheses
| Hypothesis | Verdict | Evidence |
|---|---|---|
| H1 resolution / character height | **Supported for small synthetic text; refuted as "bigger is better" for genuine text** | DX-B: synthetic numbers 0/8 → 5/8 exact at 4× (CER 0.91 → 0.41); synthetic words CER 0.87 → 0.73 (0 exact). Genuine got **worse** when upscaled: CVL 4/8 → 1/8 (2×) → 0/8 (4×); D1 CER 0.23 → 0.37. D1 crops ≥ 128 px are also worse. This points to an **optimal input-height range**, not uniform upscaling |
| H2 blur, noise, contrast, illumination | **Partly supported** | only severe levels hurt genuine text, with contrast the strongest; mild levels are within noise |
| H3 multiword lines | **Supported, but interacts with scale** | DX-C full line CER 0.87 (1×) and 0.80 (2×); oracle word crops 0.77 (1×) and **0.46 (2×)**; per-word exact 0/49 (1×) vs 8/49 (2×). Automatic geometric segmentation matched word counts on 0/8 lines (seg 2× CER 0.58) |
| H4 repeated digits and punctuation | **Weakly supported / inconclusive** | zero errors are rare (1 deletion clean; at most 7 insertions per corruption family across about 700 digit-bearing variants); digit substitutions dominate; 10% of parsed values are off by ≥ ×10; punctuation n = 17 |
| H5 borders and printed fragments | **Not supported** | DX-D line removal did not help: numbers CER 1.00 → 1.03 (1×) and 0.69 → 0.91 (2×); words unchanged. Removal probably deletes strokes that touch lines |
| H6 training-domain mismatch | **Plausible, not isolated** | synthetic words stay at 0/8 exact even at 4× and with oracle segmentation (0/8 lines exact); numbers partly recover with scale. Font domain and scale cannot be fully separated with these data |

## 4. Pipeline sanity (DX-A)
- All 245 inputs are dark ink on a light background, uint8 RGB scaled by `ToTensor`.
- 245/245 effective dimensions match the upstream `ScaleToLimitRange`.
- Token ids fall in 9–90, inside the 97-token vocabulary, and the decoder settings are unchanged.
- No implementation fault was found. A wrong polarity or channel order would not explain synthetic numbers recovering at 4×.

## 5. Amount verification
- **Synthetic dev pairs (72):** all go to review.
  - Reasons: both fields unparseable 60, written field unparseable 6, blank source field 6.
  - 0/30 matches auto-accepted and 0/36 mismatches flagged. Every stress condition also gives a review rate of 1.0.
- **GNHK pairs (2):** one accepted correctly; one numeric field unparseable.
- Recall of 1.0 here comes from abstention, not detection.

## 6. Limitations
- Dev subsets are small (DX subsets n = 8; D5 n = 3).
- Synthetic results describe font-rendered, low-resolution text.
- Constructed pairs reuse crops.
- Factors are confounded with the dataset (height with font domain, multiword with synthetic).
- The oracle word boxes come from AI visual review.
- Legibility was checked by AI, not by people.
