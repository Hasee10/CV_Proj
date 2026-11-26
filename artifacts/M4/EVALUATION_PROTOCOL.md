# M4 evaluation protocol (frozen before formal experiments)

The reference implementation is `scripts/eval_metrics.py`. Its self-test passes and covers every rule below. Changing a rule after M4 requires a dated entry in this file and must not use test results.

## Three separate levels
| Level | Question | Primary metrics |
|---|---|---|
| **A. Raw transcription** | Is the decoded text exactly what was written? | aggregate CER, WER, exact match (word recognition rate), punctuation precision, recall and F1 |
| **B. Amount value** | Does the normalised text give the correct financial value? | numeric-value exact match; written-amount value exact match |
| **C. Discrepancy detection** | Does the system flag numeric/words mismatches? | precision, recall, F1, confusion matrix, incorrect acceptance and rejection rates, manual-review rate |

A sample can be wrong at level A and right at level B; dropping a thousands separator is one example. Level A is never relaxed to hide this. Missing **decimal** points are not repaired: `125000` for `1250.00` has value 125000, which is wrong.

## Level A definitions
- **CER** = Σ character edit distance / Σ ground-truth characters (Levenshtein, unit costs).
- **WER** = Σ word edit distance / Σ ground-truth words, with whitespace tokenisation. For single words, WER = 1 − exact.
- **Exact match** is string equality, case- and punctuation-sensitive.
- **Punctuation** (`,` `.` `-` `/`) is scored by deterministic Levenshtein alignment. TP means a GT mark aligned to the identical predicted character. FN means a GT mark that was deleted or substituted. FP means a predicted mark that is extra or substituted for another character. Emitting the right number of marks in the wrong place gives TP 0.
- Raw model output is used unchanged (upstream id 3 decodes to `""`). No spaces are inserted and no case or characters are corrected. Any normalised view (case-insensitive, digits-only, space-insensitive) is labelled **secondary** and reported separately.

## Level B normalisation (fixed)
- **Numerals:** strip surrounding whitespace, a leading `Rs` / `Rs.` / `PKR` / `Rupees` / `₹` / `$`, and a trailing `/-`. Delete all commas. Then require `\d+(\.\d{1,2})?`, else unparseable (value None).
- **Written amounts:** lowercase, hyphens become spaces, whitespace tokenisation. Drop `rupees`, `rupee`, `rs`, `only`. Read units, tens, `hundred`, `thousand`, `lakh`/`lac`, `million` and `crore`, with an optional trailing `and <n> paisa|paise`. **No segmentation of unspaced text:** `fivethousandonly` is unparseable, because inserting spaces would be an amount-specific correction.
- Value equality uses `Decimal`. The GT value comes from the verified annotation, not from parsing model output.

## Level C decision rule (identical for baseline and improved)
`review` if either value is unparseable; `accept` if the values are equal; `flag` otherwise. Positive class = **mismatch**.
- **Primary (conservative):** `flag` or `review` counts as positive. Precision, recall and F1 are computed this way, along with the 2×3 confusion matrix (match/mismatch × accept/flag/review).
- **Incorrect acceptance rate** = mismatches accepted / all mismatches. This is the dangerous error.
- **Incorrect rejection rate** = matches explicitly flagged / all matches.
- **Manual-review rate** = reviews / all pairs. It is always reported next to precision and recall, because routing everything to review gives perfect recall at no value.
- **Secondary:** precision, recall and F1 on decided pairs only, with `n_decided`.
- Beam-search scores are **not** treated as probabilities. Any confidence-based abstention must first be calibrated on dev.

## Failures and coverage
- Every input is checked against the manifest SHA-256 (`smoke_inference.readable`). A mismatch, an unreadable image or a crash is recorded as a per-sample error.
- **Primary treatment:** a failed sample counts as an **empty prediction**, so its CER contribution is `len(gt)`, it is not an exact match, and at level C it goes to `review`. Report coverage, the failed count and the failure rate. Success-only metrics are secondary.
- Nothing is silently excluded. The evaluated sample count is always reported.

## Performance
Median and P95 latency (nearest-rank) per sample, covering preprocessing, encoder, beam search and rescoring, with batch size 1, excluding model load and warm-up. Also reported: total evaluation runtime, failed-inference rate, CPU model and thread count.

## Ambiguous ground truth
Keep all readings. Primary metrics use the visual reading, with alternatives reported as sensitivity analysis. Ambiguous characters are excluded from strict punctuation scoring. Writer-confirmed labels override visual readings, with the history kept (the M3-B H04/H05 precedent).

## Reporting rules
Results from exploratory (M3-B), dev and locked test sets are kept in separate tables. Baseline and improved systems use identical sample ids and paired comparisons, with the per-sample differences listed. Every stratum is reported (GNHK digit/other; custom numeric/words; per corruption and level). Nothing about generalisation is claimed beyond these sets.

---
## Amendment M4-AUDIT (2026-11-26), authorised before any formal evaluation; not based on test results
1. **Numeric grammar (strict).** The format is `[Rs|Rs.|PKR][space] INTEGER [.dd] [/-]`, case-insensitive on the prefix.
   - INTEGER is one of: `0`; `[1-9]\d*` (no grouping); international grouping `[1-9]\d{0,2}(,\d{3})+`; or South Asian grouping `[1-9]\d?(,\d{2})+,\d{3}` (for example `1,50,000`, `12,34,567`).
   - The fraction is exactly two digits.
   - Rejected (value None, which routes to review): `1,,250`, `,1250`, `1250,`, `12,50`, `1.2.3`, `1 2 5 0`, empty, `$`/`₹`/`USD` or mixed currency markers, leading zeros, one-digit fractions, `1250-00`.
   - No digit or decimal point is ever inserted or repaired.
2. **Written-amount grammar (conservative).** The structure is `[rupees] AMOUNT [and N paisa|paise] [rupees] [only]`, with at most one `rupees`.
   - Scale words are strictly decreasing and each appears at most once: Indian `crore > lakh > thousand` with multipliers 1-99, or international `million > thousand` with multipliers 1-999. The two systems are never mixed.
   - `GROUP = [1-9 hundred [and]] [1-99]`. `and` is allowed only after `hundred` or a scale word, or before the paisa fraction. Paisa must be 1-99.
   - Case-insensitive, and hyphens between words count as spaces. Commas, periods, digits, `zero`, `eleven hundred`, repeated or misordered units and scales are rejected.
   - There is no fuzzy matching, spell correction or segmentation, so unspaced output still returns None.
3. **Ground-truth values are independent of the parser.**
   - A custom `gt_value` is either the designed prompt value, used only when a human marks the field `verified` with `deviation=no`, or a human-entered `verified_value` for deviations. Otherwise it is None (`unresolved`, with a reason).
   - Pair labels (`match`/`mismatch`/`unresolved`) derive only from these values.
   - `custom_sheets.finalize` never calls the parser. A regression test enforces this.
4. **Failure-aware scoring.**
   - A record with any error, or a missing or None prediction, is scored as an empty prediction, even if a stale string remains. An empty-string prediction without an error counts as a successful (wrong) output.
   - Records with missing or empty GT are not eligible and are listed (`excluded_no_ground_truth`). Blank handwritten fields stay in the dataset as `unresolved`.
5. **Punctuation.** Rows with `punct_eligible=false` (an ambiguity note) are excluded from punctuation scoring and listed, along with the eligible row count. Alignment under minimum edit distance is a defined matching rule; it does not prove absolute positional correctness.
6. **Discrepancy metrics.**
   - Decisions must be `accept`/`flag`/`review`; anything else raises an error.
   - Labels other than `match`/`mismatch` are excluded and listed.
   - Confusion-matrix totals are asserted to equal the eligible pair count.
   - An `all_review` flag is reported, together with the review rate and the incorrect acceptance rate. An all-review system is not a working automatic verifier, even though its flag-or-review recall is 1.0.
7. **Manifests and validation.** Near-duplicate candidates across splits must be reviewed in a `--resolved` file (`not_duplicate`/`duplicate`) before a set passes. Empty manifests, missing required fields, source-hash mismatches, pairs split across dev/test and unverifiable parent lineage all fail. Reports and manifests are never overwritten.
