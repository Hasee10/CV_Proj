# M5-DEV: frozen LoGo-HTR baseline on the development split (2026-11-26)

## Scope and setup
- **Model and decoding:** the official checkpoint (SHA-256 `25db3a51…c432`), upstream preprocessing, bidirectional beam search (beam 10), `SSL_HWD_Dict.txt`, CPU, batch 1. No change to the model or decoding.
- **Data:** the dev split of the four frozen M4-FINAL manifests: 251 entries, 250 unique images, 0 inference errors. **The test split was not touched**; the runner refuses it without an explicit flag.
- **Scoring:** reproducible from the saved predictions with `scripts/score_baseline.py`.
- **Eligibility:** blank synthetic fields (6) are excluded from recognition metrics. Genuine and synthetic sets are never pooled.

## Recognition (failure-aware; coverage 100% for every group)
| Group | Eligible | Exact | CER | WER | Punctuation P / R | Amount value exact (parseable) |
|---|---|---|---|---|---|---|
| D1 GNHK words, genuine | 80 | 34 (42.5%) | 0.305 | 0.575 | 0.64 / 0.35 (7 TP, 4 FP, 13 FN) | n/a |
| D1 digit stratum | 20 | 6 | 0.383 | 0.700 | 0.60 / 0.375 | n/a |
| D1 other stratum | 60 | 28 | 0.279 | 0.533 | 1.00 / 0.25 | n/a |
| D4 CVL numeric, genuine | 90 | 38 (42.2%) | 0.185 | 0.578 | no marks in GT | 38 / 90 (83) |
| D5 GNHK integers, genuine | 2 | 1 | 0.500 | 0.500 | - | 1 / 2 (1) |
| D5 GNHK number words, genuine | 1 | 1 | 0.000 | 0.000 | - | 1 / 1 (1) |
| D6 numeric, **synthetic** | 35 | 0 | 0.993 | 1.000 | - | 0 / 35 (4) |
| D6 words, **synthetic** | 37 | 0 | 0.871 | 1.000 | - | 0 / 37 (0) |

- WER for single-token fields equals 1 − exact.
- On CVL, exact matches range from 0/9 (`5841077`) to 7/9 (`25000`) per string.
- Per-template D6 results are in `METRICS.json`: all four templates score 0 exact, with CER 0.84–1.05.
- D5 dev holds only 3 crops, so its figures carry almost no weight.

## End-to-end amount verification (dev pairs)
| Pairs | Labels | Decisions | Incorrect acceptance | Incorrect rejection | Review rate | Flag-or-review P / R / F1 | Decided-only |
|---|---|---|---|---|---|---|---|
| GNHK constructed (genuine) | 1 match, 1 mismatch | 1 accept, 1 review | 0.0 | 0.0 | 0.50 | 1.0 / 1.0 / 1.0 | 1 decided, coverage 0.5 |
| Synthetic, all | 30 match, 36 mismatch, 6 unresolved | **72 review** | 0.0 | 0.0 | **1.00** | 0.545 / 1.0 / 0.706 | 0 decided, coverage 0.0 |
| Synthetic natural | 30 match, 3 mismatch, 6 unresolved | 39 review | 0.0 | 0.0 | 1.00 | 0.091 / 1.0 / 0.167 | 0 decided |
| Synthetic constructed | 33 mismatch | 33 review | 0.0 | - | 1.00 | 1.0 / 1.0 / 1.0 | 0 decided |

**On synthetic cheques the baseline is an all-review system.** No numeric or written amount produced a parseable value pair, so every pair went to manual review. Its incorrect acceptance rate of 0 and flag-or-review recall of 1.0 come entirely from abstention. It verified no cheque automatically (0 of 30 matches accepted), and it detected no discrepancy explicitly (0 decided pairs). The two genuine GNHK pairs are too few to draw any conclusion.

## Runtime (measured)
- 232 images inferred in this run plus 18 reused from the pilot cache: 121.6 s of inference, 123.9 s wall time, model load 1.7 s.
- Median latency 0.291 s and P95 1.704 s over all 251 entries.
- By set (median / P95): D1 0.25 / 1.53 s; D4 0.31 / 0.48 s; D6 0.18 / 3.32 s, where the long words lines run 2–4.6 s.
- The slowest input was `GNHK_eng_EU_013_w024` (8.35 s; input 187×1024).

## Interpretation (descriptive; no improvement tested)
- On genuine handwriting the baseline reads about 4 in 10 dev words or digit strings exactly (D1 42.5%, D4 42.2%). Most CVL errors are single-digit substitutions, insertions or omissions in 6–7 digit strings (CER 0.185).
- On the synthetic cheque fields it fails almost completely. The crops are only 23–62 px tall, with letter heights of about 8–12 px and long multiword phrases. Upstream preprocessing keeps them at native size, which matches the M3-B scale observation and is a candidate cause to test in M6. The written outputs are pseudo-words such as `comansinsuratimen`, with no spaces.
- Punctuation stays weak: one comma was read as a decimal point (`(225,000)` → `(225.000)`, a ×1000 financial error), and separators were dropped (`25,000,000` → `2500000000`).

Locked-test evaluation is pending until the improved method is chosen and frozen.
