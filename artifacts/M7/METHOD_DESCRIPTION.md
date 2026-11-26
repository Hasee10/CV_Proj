# M7 method: Adaptive Text-Height Normalisation (ATHN)

Status: **VERIFIED on dev**. Selected configuration: **P1-A**. The locked test split was not read during M7.

## Problem it targets
M6 traced the baseline's 0/35 result on synthetic numeric amounts to scale. Those crops carry text about 14 px tall in the pixels the model sees. Genuine GNHK and CVL text sits near 45 px. Enlarging the synthetic crops 4× recovered 5 of 8 in the M6 diagnostic. Enlarging every crop 2× hurt CVL digits (4/8 to 1/8). A fixed resize therefore cannot help one group without damaging the other.

## Method
ATHN runs before the unchanged LoGo-HTR pipeline. It uses pixels only: no labels, field types or dataset names. It has no trained parameters. Source: `scripts/athn.py`.

1. **Estimate text height.**
   - Binarise with Otsu.
   - Remove long straight strokes (at least half the crop's width or height), which are printed rules.
   - Keep 8-connected components that look like characters (area at least max(4, 1e-4·h·w), height 3 px to 0.95·h, width up to 0.9·w).
   - Take the 80th percentile of their heights.
   - Return no estimate for a near-uniform crop (grey SD below 2), an ink fraction outside 0.002–0.6, or no surviving components. The crop then passes through unchanged.
2. **Decide.** If the estimate lies inside the band [24, 72] px, the crop is left unchanged.
3. **Resize.**
   - Otherwise scale isotropically by 48 / estimate, clamped to [0.5, 4.0].
   - When enlarging, cap the scale so the result stays within the upstream limits (height ≤ 256, width ≤ 1024); anything larger would be undone by the upstream transform.
   - Keep every side at least 16 px.
   - Skip changes under 5%.
   - Use INTER_CUBIC to enlarge and INTER_AREA to shrink.
4. **Recognise.** The resized crop goes through the upstream transform (ScaleToLimitRange 16–1024 × 16–256, ToTensor) and the bidirectional beam search (beam 10, max_len 200, alpha 1.0), with checkpoint `25db3a51…` unchanged.

The estimate is taken in input pixels. For the crops used here these equal the pixels the model sees, because the upstream transform only rescales crops outside 16–256 px in height or wider than 1024 px.

## Selection (frozen protocol, dev only)
The protocol ([SELECTION_PROTOCOL.md](SELECTION_PROTOCOL.md), SHA-256 in `PROTOCOL_FROZEN.sha256`) was written before any M7 inference. Four ATHN settings and one uniform-resize ablation were run on all 251 dev entries.

| config | role | D1 exact / CER | D4 exact / CER | D6 num value-exact (n=35) | guardrails |
|---|---|---|---|---|---|
| B0 | baseline | 34 / 0.305 | 38 / 0.185 | 0 | reference |
| B1 | uniform 2× (ablation) | 27 / 0.446 | 19 / 0.290 | 7 | fail (D1, D4) |
| **P1-A** | band 24–72, target 48 | **36 / 0.292** | **36 / 0.197** | **18** | **pass** |
| P1-B | band 32–64, target 48 | 34 / 0.292 | 34 / 0.206 | 18 | fail (D4) |
| P1-C | band 20–90, target 40 | 34 / 0.300 | 38 / 0.185 | 14 | pass |
| P1-D | enlarge only (ablation) | 34 / 0.321 | 36 / 0.197 | 18 | pass (not selectable) |

- P1-A and P1-C pass every guardrail. P1-A ranks first on the primary objective (18 against 14).
- The success rule (at least B0 + 3) is met.
- The D4 exact drop of 2 for P1-A sits exactly at the guardrail limit.
- Median latency stays near the baseline: 0.356 s against 0.29 s.
- The tail is much longer. The dev p95 rose from 1.70 s to 20.05 s, and the slowest single line took 360 s (see Limitations).

What the ablations show:
- **B1 (uniform 2×, no adaptivity)** loses 7 D1 and 19 D4 exact matches. Adaptivity is what protects genuine text.
- **P1-D (enlarge only, no shrinking)** matches P1-A on D4 and D6. Its D1 CER is worse (0.321 against 0.292), so shrinking oversized GNHK crops is where P1-A's D1 gain comes from.

## Word segmentation (P2): rejected
P2 adds the M6 A2 geometric word segmentation, applied to written-amount crops only. Each word is normalised and recognised on its own, and the outputs are joined with single spaces. On the 37 D6 written-amount dev lines:
- character error rate fell from 0.779 to 0.371;
- correctly parsed values rose from 0 to 1.

The frozen rule required at least 3 more correct values and a lower CER. P2 is therefore not adopted. The CER drop is large, but the recognised words still rarely form a parseable amount.

## What did not change
- Written amounts on synthetic cheques: 0/37 parse in both B0 and P1-A.
- As a result, all 72 synthetic dev pairs still go to review, as they did for the baseline. ATHN improves numeric-amount reading. It does not yet enable automatic numeric-vs-words decisions on this data.

## Limitations
- **Latency.** On enlarged wide written lines, the decoder often hallucinates text until it nears the 200-token limit. These lines take 10 to 48 s on the i7-1265U CPU, and one took 360 s. The median is unaffected; the tail is not.
- **Synthetic data.** The primary objective is measured on font-rendered synthetic cheques (n = 35 on dev). Gains there do not show gains on real handwritten cheques.
- **Selection.** The three candidate bands were chosen from dev text-height statistics. Test-split behaviour is measured once, in M8.
