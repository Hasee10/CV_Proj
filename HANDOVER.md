# ChequeVerify handover (start here)

State at the end of the backend work, 27 Nov 2026:
- The research and the backend are finished and frozen.
- The frontend, the full application integration, the report and the presentation are still to do.

This file is the entry point; the other documents cover one topic each.

| need | document |
|---|---|
| install and run the backend | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| endpoints, fields, errors | [API_CONTRACT.md](API_CONTRACT.md), [openapi.json](openapi.json), real responses in [artifacts/M10/examples/](artifacts/M10/examples/) |
| what the frontend must do | [FRONTEND_REQUIREMENTS.md](FRONTEND_REQUIREMENTS.md) |
| a ready prompt for a frontend coding session | [FRONTEND_PROMPT.md](FRONTEND_PROMPT.md) |
| a live demo script | [DEMO_GUIDE.md](DEMO_GUIDE.md) |
| full evaluation | [artifacts/M8/FINAL_EVALUATION_REPORT.md](artifacts/M8/FINAL_EVALUATION_REPORT.md) |
| method and its selection | [artifacts/M7/METHOD_DESCRIPTION.md](artifacts/M7/METHOD_DESCRIPTION.md) |
| reproduction and repository audit | [artifacts/FINAL_BACKEND_HANDOVER/](artifacts/FINAL_BACKEND_HANDOVER/) |

## Objective
A cheque carries the amount twice, in figures and in words. ChequeVerify reads both handwritten fields, converts each to a value, and compares them:
- `accept` when they agree;
- `flag` when they differ;
- `review` when either field cannot be read.

It is a computer-vision course project and a prototype for human review. It is not bank software. It does not detect fraud, and agreement of the two amounts does not show that a cheque is genuine.

## Paper and original model
- **Paper:** S. Mitra, A. Mondal, C. V. Jawahar, "Learning Beyond Labels: Self-Supervised Handwritten Text Recognition", WACV 2026.
- **Recogniser:** LoGo-HTR, the authors' released downstream checkpoint (Hugging Face `Shree10/LoGo-HTR`, SHA-256 `25db3a51…c432`, 6,385,537 parameters).
- **Code:** upstream at github.com/shreemitra/LoGoHTR, commit `9eaea5fe`, MIT licence.

We use the checkpoint for inference only, on CPU, with no retraining and no change to its weights, preprocessing or beam search (beam 10, max length 200). Licences for code, checkpoint and datasets are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the README.

## Our contribution
1. **Evaluation set-up (M4–M5).** A frozen benchmark of genuine handwriting (GNHK words and numbers, CVL digit strings) and synthetic cheque fields:
   - strict Decimal parsers for numeric and English written amounts;
   - an accept/flag/review rule;
   - a locked test split.
2. **Failure analysis (M6).** 3,675 stress variants and diagnostics. These showed that the baseline fails on synthetic cheque fields mainly because their text is too small (about 14 px tall, against about 45 px for genuine text).
3. **ATHN, adaptive text-height normalisation (M7).** A training-free step before the unchanged model:
   - it estimates text height from the pixels;
   - crops between 24 and 72 px are left alone;
   - other crops are resized toward 48 px, with the scale limited to 0.5–4.0.

   It was chosen on the dev split under a protocol frozen beforehand. Rejected alternatives, recorded as negative results: uniform 2× upscaling (harmed genuine text) and word segmentation (lowered written-line CER but did not yield correct values).
4. **Locked-test evaluation (M8)**, with paired cluster-bootstrap intervals and McNemar tests.
5. **Backend (M9-A, M10-A)**: a FastAPI service with both modes, the verification flow and security limits.

## Findings (locked test split, baseline → ATHN)
| measure | baseline | ATHN |
|---|---|---|
| synthetic numeric CER | 1.014 | 0.599 |
| synthetic numeric correct values | 0/77 | 17/77 |
| GNHK words CER | 0.296 | 0.252 |
| GNHK words exact | 73/160 | 78/160 |
| CVL digits CER | 0.141 | 0.143 |
| CVL digits exact | 97/210 | 97/210 |
| genuine handwriting, aggregate CER change | | −0.015, 95% CI [−0.036, 0.002] |
| GNHK constructed pairs decided automatically | 24/52 | 27/52 (no mismatch accepted by either) |
| synthetic pairs | all review | all review |
| synthetic written amounts read to the correct value | 0 | 0 |

How to read these:
- **Synthetic numerics:** the gain is clear; its 95% interval is [−0.534, −0.296] in CER.
- **Genuine handwriting:** the interval includes zero. No significant gain or harm was found. That is not proof that the two methods are equivalent, and no non-inferiority test was done.
- **Synthetic cheques:** amount verification stays all-review, because no synthetic written amount is read correctly.

## Scientific limitations
- The large gain is on font-rendered synthetic data from one public set. No real handwritten cheques were available with consent.
- The genuine test groups are small: GNHK pairs 52, GNHK numbers 43, GNHK words 26.
- CVL writer ids were inferred.
- One CPU machine and one run.
- Latency: see below.

## Backend architecture
```
HTTP client
  -> backend/app.py     FastAPI: upload/ROI validation, structured errors, CORS, timeouts, request-id logging
  -> backend/engine.py  loads the model once per process; baseline/proposed dispatch; one inference slot
                        (CV_MAX_CONCURRENCY); Decimal parsing; accept/flag/review with reasons
  -> scripts/smoke_inference.py  hash-checked weights_only checkpoint load, upstream transform, runtime adapters
     scripts/athn.py             the frozen ATHN step (proposed mode)
     scripts/eval_metrics.py     strict numeric and written-amount grammars, decision rule
  -> third_party/LoGoHTR         unmodified upstream model code (git-ignored, pinned commit)
```
- Images are processed in memory and never written or kept.
- Logs carry request id, path, status and time, never image content or recognised text.
- `GET /api/benchmark` serves the saved M8 metrics file.

## Repository structure
```
backend/            FastAPI service (app.py, engine.py)
scripts/            research pipeline, ATHN, parsers, live check, demo builder
tests/              research suites (test_m4_* ... test_m8) and backend suites (test_backend_*)
artifacts/M3_A..M10 per-milestone evidence; FINAL_BACKEND_HANDOVER/ reproduction and audit
data/benchmarks/    frozen evaluation crops and manifests (GNHK, CVL, synthetic)
data/demo/          three composite demo sheets with exact ROIs
third_party/, models/  upstream code and checkpoint (git-ignored; see SETUP_GUIDE.md)
```

## Milestones
| milestone | state |
|---|---|
| M3–M6: model check, datasets, baseline, failure analysis | complete |
| M7: technical contribution (ATHN) | complete |
| M8: comparative evaluation | complete |
| M9-A: backend | complete |
| M10-A: backend integration and handover | complete. A fresh-clone reproduction passed, using cached external dependencies; see the reproduction report. |
| M9-B: frontend | pending (collaborator) |
| M10-B: full application integration | pending |
| report (3 Dec) and presentation with live demo (4 Dec) | pending |

## Frontend responsibilities
- Build the UI described in [FRONTEND_REQUIREMENTS.md](FRONTEND_REQUIREMENTS.md), in a new `frontend/` folder.
- Do not change `backend/`, `scripts/`, `artifacts/`, `data/` or any result.
- [FRONTEND_PROMPT.md](FRONTEND_PROMPT.md) is a ready prompt for a Claude Code session.
- The backend allows CORS from `http://localhost:5173` by default. Set `CV_CORS_ORIGINS` for other origins.

## Known latency limitation
- Proposed mode is fast on numeric crops but slow on enlarged written-amount lines. On the locked test, 75 of 89 such lines took over 10 s, 5 took over 120 s, and the longest took 419 s.
- The default timeout is 120 s (`CV_INFERENCE_TIMEOUT_S`). At the deadline the server answers 504, but the running model call cannot be interrupted. It keeps the single inference slot until it finishes, and other requests meanwhile get 503 `busy` after a capped wait.
- Running calls never exceed `CV_MAX_CONCURRENCY`, and an abandoned request never starts a model call later; slow-inference tests cover both.
- Baseline mode stays available for every request. For live demos, use baseline for full verifications (see [DEMO_GUIDE.md](DEMO_GUIDE.md)).

## Start the backend
```powershell
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
First-time setup is one command, `py -3.11 scripts/setup_env.py`, which ends with `SETUP COMPLETE`. Manual steps, the checkpoint hash, smoke tests and troubleshooting are in [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Protection against accidental changes
Only `frontend/` and four status documents (`README.md`, `PROJECT_TRACKER.md`, `ROADMAP.md`, `PROJECT_CONTEXT.md`) may change. Three layers enforce this:
- `.claude/settings.json` denies Claude Code edits to frozen paths;
- a git pre-commit hook (`scripts/guard.py --staged`, enabled by the setup script) refuses commits that touch frozen files, weights, archives, build output, `.env` files or token-like secrets;
- `python scripts/guard.py --verify` checks every frozen file against the SHA-256 values in `FROZEN_MANIFEST.json`.

The project owner can still commit a deliberate change with `git commit --no-verify`. `CLAUDE.md` explains the rules to every Claude Code session.
