# Handover: ChequeVerify backend and results (after M10-A)

This is the state at the end of the backend milestone. The frontend has not been started; [FRONTEND_REQUIREMENTS.md](FRONTEND_REQUIREMENTS.md) says what it needs. Nothing here has been pushed to GitHub. The collaborator who owns pushes should push the local commits listed at the end.

## Run the backend
```powershell
.venv\Scripts\python.exe -m pip install -r requirements-inference.txt -r requirements-backend.txt
.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
- Startup loads the checkpoint once, which takes a few seconds on the development laptop. It needs `models/logo_htr/Downstream_Full_Model_Best.ckpt` (SHA-256 `25db3a51…`) and the upstream code in `third_party/LoGoHTR` at commit 9eaea5fe. Both are git-ignored; [README.md](README.md) explains how to fetch them.
- Without the checkpoint the server still starts. `/health` and the inference endpoints then return 503.
- Settings are environment variables; [.env.example](.env.example) lists them with their defaults. No secrets are needed.
- Swagger UI is at http://127.0.0.1:8000/docs. The exported schema is [openapi.json](openapi.json). The written contract is [API_CONTRACT.md](API_CONTRACT.md).

## What the API does
| endpoint | purpose |
|---|---|
| `GET /health` | model loaded or not |
| `GET /api/model-info` | checkpoint hash, settings, modes, stated limitations |
| `POST /api/recognize` | one crop, `field_type` numeric or written, `mode` baseline or proposed |
| `POST /api/verify` | two crops, or one cheque image plus two user-drawn normalised boxes; returns accept / flag / review with reasons |
| `GET /api/benchmark` | the saved M8 locked-test comparison; never recomputed |

The two modes:
- `baseline` is the unmodified LoGo-HTR pipeline.
- `proposed` adds ATHN (adaptive text-height normalisation, frozen config P1-A) before the same model. It is the default, a choice declared before the test evaluation.

## Results to quote
Numbers are on the locked test split ([artifacts/M8/FINAL_EVALUATION_REPORT.md](artifacts/M8/FINAL_EVALUATION_REPORT.md)), baseline → proposed:
- **Synthetic numeric amounts:** correct value 0/77 → 17/77. CER 1.014 → 0.599, 95% CI of the change [−0.534, −0.296].
- **Genuine handwriting (GNHK and CVL, 439 items):** CER change −0.015, CI [−0.036, 0.002]. 19 exact improvements against 10 regressions (p = 0.136). Read this as no measurable harm and a possible small gain.
- **GNHK amount pairs (52):** automatic decisions rose from 24 to 27. Incorrect acceptance stayed at 0 for both.
- **Synthetic pairs (164):** every pair goes to review with both methods, because no synthetic written amount is read well enough to parse.
- **Latency per crop:** median 0.25 → 0.29 s, but enlarged written lines often take 10–48 s. 5 of 89 test lines took over 120 s; the slowest took 419 s.

## Known issues the demo must respect
1. **Proposed mode on a written amount can be slow.** In the live check, verifying a full synthetic cheque took 37.7 s. Requests past `CV_INFERENCE_TIMEOUT_S` (120 s) return 504. For a smooth live demo, use genuine-handwriting crops or `mode=baseline` for written fields. This is a measured property of the frozen method, not a bug to patch quietly; changing it would need a new dev selection.
2. **Synthetic written amounts never parse.** Verifying a synthetic cheque therefore returns `review`. The demo should show `review` as the correct conservative outcome.
3. **The server does not find fields itself.** The user draws the two boxes.
4. **`accept` is not proof of authenticity**, and the beam score is not a confidence. Keep these warnings visible in the UI.

## Evidence and where it lives
| milestone | status | commit | key artifacts |
|---|---|---|---|
| M7 method selection (dev only) | VERIFIED | f836129 | `artifacts/M7/` (protocol, ablations, FROZEN_CONFIG.json) |
| M8 locked test evaluation | VERIFIED | 5520d75 | `artifacts/M8/` (report, statistics, figures) |
| M9-A backend | VERIFIED | 56b9df1 | `backend/`, `artifacts/M9/TEST_RESULTS.json` |
| M10-A live check and handover | VERIFIED | this commit | `artifacts/M10/LIVE_HTTP_CHECK.json`, this file |

Tests:
- `tests/test_m8.py`: 7/7, running the M7, M6, M5 and M4 suites inside.
- `tests/test_backend_unit.py`: 17/17, mocked inference.
- `tests/test_backend_integration.py`: 7/7, real checkpoint.
- Live HTTP check: 13/13.

Every API example in `artifacts/M10/examples/` was written by a real request in the integration tests.

## Not done
- The frontend (by design: it belongs to the collaborator).
- The optional held-out stress subset in M8.
- ATHN restricted to numeric fields. It is a plausible fix for the latency tail, but it would be a new method and needs its own dev selection.
- Field detection on full cheques, real handwritten cheques (none available with consent), and GPU deployment.
