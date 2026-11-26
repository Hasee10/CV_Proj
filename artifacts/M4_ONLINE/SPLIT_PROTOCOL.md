# M4-ONLINE split protocol (seed 20261126)

| Set | Unit | Algorithm | Counts (dev / test) | Writer-disjoint? |
|---|---|---|---|---|
| D1 GNHK subset | page | unchanged (M4): sorted test pages, seeded shuffle, first 30% (52 pages) dev | 80 / 160 | not verifiable (no writer ids) |
| D4 CVL | inferred writer | the 121 ids that have all 10 strings, sorted and shuffled with the seed; the first 30 are used, of which the first 9 go to dev and the next 21 to test | 90 / 210 (9 / 21 writers) | yes, under the inferred writer id |
| D5 GNHK pairs | page | re-derived with the identical D1 rule; asserted equal to the frozen D1 page assignment; pairs built only within a split | 3 / 69 crops, 2 / 52 pairs | not verifiable |
| D6 synthetic | cheque | sorted row indices, seeded shuffle, first 30% (39 cheques) dev; constructed mismatches only within a split | 78 / 182 crops, 72 / 164 pairs | n/a (synthetic; templates shared across splits) |

## Leakage checks (`artifacts/M4_ONLINE/VALIDATION_REPORT.json`, all 4 manifests validated together: passed)
- 872 samples, 287 groups, 0 errors. No group, writer or pair spans splits.
- 0 unresolved cross-split exact or near duplicates. All 227 candidates were synthetic and were resolved by rule (`data/benchmarks/duplicate_review.json`).
- D5 crops that are byte-identical to D1 samples (3) sit in the same split.
- All 290 pairs: both crops exist, share the pair's split, and carry a label consistent with the independent values. Natural pairs come from one cheque; constructed pairs come from two sources.

## Rules carried forward
- M3-B stays exploratory and development-only.
- Test labels, splits and manifest hashes are frozen before comparative evaluation.
- Improvements are selected on dev only.
- Baseline and improved systems use identical ids.
- Constructed pairs reuse crops, so they are **not independent handwriting samples**. Per-crop and per-pair metrics are reported separately, and pair-level uncertainty must account for the reuse.
- D5 dev contains a single word crop, which is too small for tuning. Dev tuning should rely on D1, D4 and D6 dev, with D5 used as test-only evidence.
- Recognisers receive image crops only: never prompts, labels, values or pair metadata.
