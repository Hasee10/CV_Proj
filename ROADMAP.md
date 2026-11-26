# ChequeVerify roadmap

This file is for everyone working on the repository. It lists each phase, what it must produce, what counts as done, and what is already finished. `PROJECT_TRACKER.md` remains the dated log of decisions; this file is the plan.

## Deadlines

| Date | Submission |
|---|---|
| 2 Dec 2026 | implementation, models and dataset |
| 3 Dec 2026 | research report and documentation |
| 4 Dec 2026 | presentation (PPTX) and live demonstration |

The course requires a reproducible baseline from the selected paper, standard and stress-test data, a systematic failure analysis, a justified improvement, a baseline-versus-improved comparison, and a live demo.

## Phase overview

| Phase | Goal | Status | Target date (proposed) | Owner |
|---|---|---|---|---|
| M0 | Read the course requirements | done | 26 Nov | |
| M1 | Review the candidate papers | done | 26 Nov | |
| M2 | Select the paper (LoGo-HTR, WACV 2026) | done | 26 Nov | |
| M3-A | Run the released checkpoint on CPU | done | 26 Nov | |
| M3-B | Test it on independent handwriting | done | 26 Nov | |
| M4 | Datasets, splits and evaluation protocol | done | 26 Nov | |
| M5 | Baseline evaluation | next | 27 Nov | |
| M6 | Stress tests and failure analysis | planned | 28 Nov | |
| M7 | Improvement (design and implementation) | planned | 29 Nov | |
| M8 | Baseline vs improved comparison and ablations | planned | 30 Nov | |
| M9 | Web demo | planned | 30 Nov – 1 Dec | |
| M10 | Reproducibility pass and final tests | planned | 1 Dec | |
| M11 | Research report | planned | 2–3 Dec | |
| M12 | Slides and live demo | planned | 3–4 Dec | |

Owners are blank on purpose. Put your GitHub handle next to the phase you take.

## Completed phases

**M0–M2.** We use one paper, as the instructor allows: LoGo-HTR (Mitra, Mondal and Jawahar). Its released downstream checkpoint lets us run inference without training. ProtoSig was dropped.

**M3-A** (`artifacts/M3_A/`). The checkpoint loads strictly on CPU: all 673 tensors, 6,385,537 parameters. It read 8/8 preselected words, at a median of 0.14 s per word. The vocabulary file was identified by experiment (`SSL_HWD_Dict.txt`).

**M3-B** (`artifacts/M3_B_final/`). On nine photographed samples from one writer, neutral crops gave 4/9 exact matches and CER 0.2647, while full photos gave 1/9. The model never produced a comma, a decimal point or a space. These are observations, not accuracy figures.

**M4** (`artifacts/M4/`, `M4_AUDIT/`, `M4_ONLINE/`). Evaluation data, all with seed `20261126` and validated together (872 samples):

| Set | Type | Dev / test |
|---|---|---|
| GNHK word subset | genuine | 80 / 160 |
| CVL digit strings | genuine, split by writer | 90 / 210 |
| GNHK number-word pairs | genuine, constructed pairs | 2 / 52 pairs |
| Synthetic cheques | font-rendered | 72 / 164 pairs |

Metric code, amount parsers and stress corruptions are frozen, with 38 regression tests. No genuine handwritten cheque dataset was downloadable, so cheque-level results come from synthetic data and are always reported separately.

## M5: baseline evaluation

Run the unchanged baseline on every set and record the numbers the improvement will be judged against.

- Baseline: the official checkpoint, `SSL_HWD_Dict.txt`, upstream preprocessing and beam search (beam 10). No changes. Definition in `artifacts/M4/BASELINE_DEFINITION.md`.
- Run `scripts/smoke_inference.py` on each manifest, with a new `--out` path under `artifacts/M5/`.
- Score with `scripts/eval_metrics.py`, covering:
  - CER and WER;
  - exact match;
  - alignment-based punctuation;
  - numeric and written amount values;
  - discrepancy precision, recall, F1, incorrect acceptance and review rate;
  - median and P95 latency.
- Report dev and test in separate tables, and genuine and synthetic sets in separate tables.
- Estimated CPU time is roughly 5–20 minutes for all 872 clean crops, based on M3 latencies. Measure it; do not drop samples to save time.

Done when every sample has a recorded prediction or a recorded error, the metrics come from the frozen code, and `artifacts/M5/SUMMARY.json` holds the commands and hashes.

## M6: stress tests and failure analysis

Find where the baseline fails, and why, using dev data.

- Generate paired corruptions with `scripts/stress_corrupt.py`: low resolution, blur, uneven lighting, low contrast and noise, at 3 levels each. Output goes to a new empty folder.
- Compare each variant with its clean parent. Group the errors by type: missing punctuation, missing spaces, repeated zeros, substitutions, scale.
- Keep synthetic corruption results apart from naturally hard photos.

Done when there is a per-condition table and a failure write-up with examples and evidence for each root cause.

## M7: improvement

Pick and build one training-free improvement that targets a failure M6 measured. Candidates from the early results, all still unproven:

- normalise text height before inference, since larger crops did worse and ran slower;
- split written amounts into words, since single words were read and full lines were not;
- quality-aware enhancement for low-contrast or blurred photos;
- send uncertain amounts to human review.

Choose only on dev results. The improved system may use the same crops as the baseline. It may not use prompts, labels or anything else the baseline does not get. No model training.

## M8: comparison and ablations

Run baseline and improved systems once on the locked test sets, on identical sample ids. Report paired differences per set and per condition, the cost in latency, and an ablation for each part of the improvement. Never use test results to change the method.

## M9: web demo

A small local web app: upload a cheque image or amount crops, run baseline and improved side by side, show both readings, the parsed values and the accept / flag / review decision. It must run on a laptop CPU and show at least one case the improvement fixes. Template or manual cropping is acceptable; automatic field detection is out of scope unless time allows.

## M10: reproducibility

From a fresh clone, follow the README, fetch the checkpoint and data, run all tests, and reproduce the M5 and M8 tables. Fix anything that does not reproduce. Write install and run instructions for both systems.

## M11 and M12: report and presentation

The report follows the course structure: abstract, introduction, literature review, baseline method, datasets including the stress sets, failure analysis, proposed improvement, implementation, results with ablations, discussion and limitations, conclusion, references. The slides (10–15 minutes) cover the problem, baseline, failures, the change, the results and a live before/after demo. Plan for questions on every design choice.

## Rules for contributors

- Work on a branch per phase (for example `m5-baseline`) and open a pull request to `main`.
- Put evidence in `artifacts/<phase>/`: a `SUMMARY.json`, a `COMMANDS.md`, logs and hashes. Never overwrite an earlier phase's files; the scripts refuse to.
- Do not commit the checkpoint, `.venv/`, `third_party/`, `research/` or raw dataset caches (`.gitignore` covers them).
- Tune on dev only. Run the test splits once per finished system.
- Report failures as they are. No cherry-picked examples and no invented numbers.
- Before pushing, run `tests/test_m4_online.py`; it also runs the M4 audit suite.
- Keep `THIRD_PARTY_NOTICES.md` current when you add code, data or models.

## Known limitations to keep in view

- The checkpoint's training data is unknown, so overlap with GNHK cannot be ruled out.
- Genuine written amounts are limited to 27 single number words.
- All crops come from known positions; there is no automatic cheque-field detection yet.
- Signature verification and tampering detection are out of scope.
