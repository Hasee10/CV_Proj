# M8 final evaluation: frozen baseline against ATHN (P1-A) on the locked test split

**Status:** VERIFIED. Both methods ran once on the same 621 test entries. Nothing was tuned after the test split was opened. The proposed configuration is byte-identical to `artifacts/M7/configs/P1-A.json`, frozen in commit f836129 before this run.

## Setup
- **Data** (counts checked against the frozen M4-FINAL manifests): 621 entries.
  - D1 GNHK words: 160.
  - D4 CVL digit strings: 210.
  - D5 GNHK number crops: 69 (43 numeric, 26 words).
  - D6 synthetic cheque crops: 182.
- 603 entries are recognition-eligible. The 18 blank synthetic fields (14 numeric, 4 written) are reported but not scored.
- **Pairs:** 216 amount pairs (52 GNHK constructed, 164 synthetic). 18 synthetic pairs have no verified label and are excluded from pair metrics.
- **Model:** checkpoint `25db3a51…`, upstream commit 9eaea5fe, CPU (i7-1265U, 10 threads).
- **Baseline:** upstream transform only.
- **Proposed:** ATHN band 24–72 px, target 48 px, scale 0.5–4.0. It resized 290 of 621 crops. The rest took the identity path, and their predictions match the baseline exactly (tested).
- **Metrics:** failure-aware, meaning a failed inference counts as an empty prediction. No inference failed in either run (coverage 1.0).
- **Statistics:** a cluster bootstrap over `group_id` (GNHK page, CVL writer, cheque; 10,000 resamples, seed 20261126) gives 95% intervals for the change in aggregate CER and exact count. An exact two-sided McNemar test is run on discordant items. No multiplicity correction is applied, so the p-values are descriptive.

## Recognition results
| dataset (eligible n) | CER base → ATHN | change [95% CI] | exact base → ATHN | Δ pp | improved / regressed | McNemar p |
|---|---|---|---|---|---|---|
| D1 GNHK words (160) | 0.296 → 0.252 | −0.044 [−0.095, 0.005] | 73 → 78 | +3.1 | 11 / 6 | 0.332 |
| D4 CVL digits (210) | 0.141 → 0.143 | +0.002 [−0.003, 0.009] | 97 → 97 | 0.0 | 2 / 2 | 1.0 |
| D5 GNHK numbers (43) | 0.412 → 0.353 | −0.059 [−0.160, 0.035] | 27 → 30 | +7.0 | 4 / 1 | 0.375 |
| D5 GNHK words (26) | 0.242 → 0.221 | −0.021 [−0.109, 0.132] | 11 → 12 | +3.8 | 2 / 1 | 1.0 |
| D6 synthetic numeric (77) | 1.014 → 0.599 | −0.414 [−0.534, −0.296] | 0 → 17 | +22.1 | 17 / 0 | 1.5e-05 |
| D6 synthetic written (87) | 0.923 → 0.827 | −0.095 [−0.210, 0.043] | 0 → 0 | 0.0 | 0 / 0 | 1.0 |
| all genuine (439) | | −0.015 [−0.036, 0.002] | | | 19 / 10 | 0.136 |

Relative CER reduction: D1 14.8%, D4 −1.6%, D5 numeric 14.3%, D5 words 8.7%, D6 numeric 40.9%, D6 written 10.3%.

WER, base → ATHN:
- D1: 0.544 → 0.513.
- D4: 0.538 → 0.538.
- D6 numeric: 1.000 → 0.779.

Punctuation (D1 only, the one group with punctuation in its ground truth): precision 0.50 in both methods; recall 0.13 → 0.22.

**Amount values** (strict grammar, Decimal comparison):

| group | correct value, base → ATHN | parseable, base → ATHN |
|---|---|---|
| D6 numeric | 0/77 → 17/77 (+22.1 pp) | 5 → 49 |
| D4 | 97/210 → 97/210 | |
| D5 numeric | 27/43 → 30/43 | |
| D5 words | 15/26 → 16/26 | |
| D6 written | 0/87 → 0/87 | 0 → 0 |

Only the synthetic numeric change is clearly separated from zero. On genuine handwriting the direction is favourable: 19 exact improvements against 10 regressions. Every interval for genuine data still includes zero, so the evidence is consistent with "no harm, possible small gain", not with a demonstrated gain. D4, where the dev guardrail was tight, ended exactly level on test.

## Amount-pair verification
| subset | method | accept / flag / review | incorrect acceptance | incorrect rejection | review rate | flag-or-review P / R / F1 | decided-only P / R / F1 (n) |
|---|---|---|---|---|---|---|---|
| GNHK constructed (52) | base | 11 / 13 / 28 | 0.000 | 0.115 | 0.538 | 0.634 / 1.000 / 0.776 | 0.769 / 1.000 / 0.870 (24) |
| GNHK constructed (52) | ATHN | 12 / 15 / 25 | 0.000 | 0.077 | 0.481 | 0.650 / 1.000 / 0.788 | 0.867 / 1.000 / 0.929 (27) |
| synthetic, labelled (146) | base | 0 / 0 / 146 | 0.000 | 0.000 | 1.000 | 0.575 / 1.000 / 0.730 | none decided |
| synthetic, labelled (146) | ATHN | 0 / 0 / 146 | 0.000 | 0.000 | 1.000 | 0.575 / 1.000 / 0.730 | none decided |

On GNHK pairs, ATHN made three more automatic decisions:
- explicit mismatch detection rose from 10 to 13;
- automatically accepted true matches rose from 11 to 12;
- no mismatch was accepted by either method.

Over all 198 labelled pairs, correct automatic decisions improved for 6 pairs and regressed for 2 (McNemar p = 0.289).

The synthetic pairs show no change. Every synthetic written amount still fails the words grammar, so every synthetic pair still goes to review, with both methods. Decision coverage there is 0. The flag-or-review recall of 1.0 is a direct result of routing everything to review; it is not a detection ability.

## Runtime (CPU, per unique input)
| | median | p95 | over 10 s | over 120 s | max |
|---|---|---|---|---|---|
| baseline | 0.251 s | 1.04 s | 0 | 0 | 5.96 s |
| ATHN | 0.294 s | 19.0 s | 75 | 5 | 419 s |

ATHN's own preprocessing costs 1.3 ms at the median. The tail comes from the 89 resized synthetic written lines: 75 of them took over 10 s and 5 over 120 s. On these wide, enlarged lines the beam search explores long hallucinated hypotheses. The backend's default timeout is 120 s, so these 5 lines would return 504 in proposed mode. No other category took over 10 s. Total wall time: baseline 243 s, ATHN 3,115 s.

## Interpretation
- ATHN fixes the scale failure M6 diagnosed for synthetic numeric amounts. On genuine handwriting it gives a small, non-significant improvement and no measurable harm.
- It does not make written amounts on synthetic cheques readable. Automatic cross-checking of numeric against written amounts therefore stays unavailable on that data.
- The cost is a heavy latency tail on exactly the inputs where it does not help: written lines enlarged up to 4×.

A follow-up worth testing would apply ATHN to numeric fields only. That would be a new method and needs a fresh dev selection; it was not tried here, because this evaluation is post-test.

## Limitations
- The large gain is on font-rendered synthetic data from one Hugging Face set; no real handwritten cheques were available.
- Small genuine groups (D5: 43 and 26 items) have wide intervals.
- CVL writer ids are inferred.
- Single CPU, one run. Latency depends on the machine, and other processes were active during parts of the run.
- The optional supplementary held-out stress subset was not run, to keep compute on the required locked-test comparison.

## Figure checks
All figures were opened and compared with the JSON values. Two changes were made to the analysis script, both before this report: p-values are printed to 3 significant figures, and the McNemar p-value for 17/0 is 1.5e-05 rather than a rounded 0.0.
- `figures/test_cer_exact.png`: bars match `COMPARATIVE_METRICS.json` (for example, D6 numeric exact rate 17/77 = 0.22; D5 numeric 30/43 = 0.70).
- `figures/test_cer_delta_ci.png`: points and whiskers match `STATISTICAL_ANALYSIS.json`. Only D6 numeric excludes zero.
- `figures/test_pair_decisions.png`: stacks match the decision counts above (GNHK 11/13/28 against 12/15/25; synthetic 164 review).
- `figures/test_latency.png`: shows the long ATHN tail up to 419 s.
- The six M6 figures checked in this milestone agree with the M5/M6 JSON:
  - `cer_vs_severity`, `exact_vs_severity`: clean D1 0.425 exact / CER 0.305; D4 0.422 / 0.185.
  - `degradation_heatmap`: D1 blur s3 +0.72; D4 contrast s3 +0.29.
  - `diagnostics`: DX-C oracle 2× CER 0.457; full line 2× 0.799.
  - `error_categories`: D6 written missing_space and multiword_collapsed both 37, equal to all eligible dev lines.
  - `error_vs_geometry`: synthetic numeric points lie below 20 px estimated ink height; genuine D1 and D4 points spread over about 13–150 px.
