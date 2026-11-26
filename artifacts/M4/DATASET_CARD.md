# ChequeVerify evaluation datasets: dataset card

| Set | Role | Status | Samples | Writers | Location |
|---|---|---|---|---|---|
| D1 GNHK subset | standard public benchmark (word level) | **acquired** | 240 (dev 80 / test 160) | unknown (122 pages) | `data/public/gnhk/subset/` + `manifest.json` |
| D2 Custom amounts | banking-domain paired numeric + words | **designed, NOT collected** | 0 (planned 168–252 crops from 4–6 writers) | 0 | `data/custom/` |
| D3 Synthetic stress | paired corruptions of D1/D2 | **protocol frozen, NOT generated** | 0 (15 variants per clean sample when run in M6) | inherits | `scripts/stress_corrupt.py` |
| D0 M3-B exploratory | development-only feasibility data | acquired (M3-B) | 9 handwriting samples (21 condition entries) | 1 (student, W01) | `artifacts/M3_B_final/` |

## D1 GNHK subset
- Source: GNHK test split, CC-BY-4.0. Mirror and provenance are in `DATASET_SELECTION.md`.
- Format: PNG RGB crops, the axis-aligned box of the official word polygon on the EXIF-transposed page. Annotation crops, not automatic segmentation.
- EXIF orientation: 29 test pages carry tag 6 or 8. The polygons are in displayed (transposed) coordinates, so pages are transposed before cropping. Tags of used pages: 1:43, none:38, 6:18, 0:12, 8:10, 3:1.
- Labels: GNHK `text` field as published, with no correction.
- Statistics: dev 80 words (377 GT chars, 14 with punctuation, 42 pages); test 160 words (706 chars, 18 with punctuation, 80 pages). Regions: AF/AS/EU/NA.
- Preprocessing for evaluation: none beyond the crop. The model's own upstream transform applies.
- Ethics: public CC-BY-4.0 data. The GNHK authors offer removal on request, and we carry no personal data beyond the handwriting itself.

## D2 Custom handwritten amounts (design)
- 21 amount pairs per writer on 3 printed sheets (A, B, C): 15 matching and 6 deliberately mismatching numeric-versus-words pairs. Features covered: small and large integers, repeated zeros, thousands separators, decimals, currency (`Rs.`, `PKR`, `/-`), lakh, paisa, transpositions, magnitude errors. The full list is `data/custom/template/amount_list.csv`.
- Fictional sheets labelled "NOT A CHEQUE". No names, signatures, account numbers or IDs. Writers are anonymous (`W01`…).
- Ground truth: what was actually written (verified per crop). The pair label is derived from the verified values, never from model output.
- Crops: template-registered (ArUco homography plus fixed boxes). This is a deterministic geometric extraction with known layout, not a learned detector.

## D3 Synthetic stress (design)
5 corruptions × 3 severities, a fixed seed per variant, kept separate from naturally difficult handwriting. See `STRESS_TEST_PROTOCOL.md`.

## Not claimed
No dataset here is a statistically representative sample of real bank cheques. No custom data exists yet. The checkpoint's training data is unknown, so no set is guaranteed unseen.
