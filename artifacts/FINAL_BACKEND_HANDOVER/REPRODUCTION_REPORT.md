# Fresh-clone reproduction report (27 Nov 2026)

**Result:** isolated-clone reproduction passed, using cached external dependencies. A cold install on a new machine was not tested.

## What "reproduction" means here
| level | status | detail |
|---|---|---|
| isolated clone of the committed repository | passed | `git clone` of the local repository into an empty temporary folder. The original working copy was not modified. |
| external dependencies from local caches | used | Three items came from local copies rather than downloads; see "External dependencies" below. |
| cold install (fresh machine, downloads from PyPI, GitHub and Hugging Face) | not tested | The commands are in SETUP_GUIDE.md, but nobody has run them on a clean machine. |

External dependencies:
- **Upstream code:** cloned from the local copy of `third_party/LoGoHTR` and checked out at `9eaea5fe52e9…`.
- **Checkpoint:** copied from `models/`, SHA-256 `25db3a51…c432` checked after copying.
- **Python:** the existing project venv was reused. Its 58 installed packages are exactly the union of `requirements-inference.txt`, `requirements-backend.txt` and `requirements-analysis.txt`, same versions, nothing extra or missing, and `pip check` is clean.

Machine: Windows 11 Pro 10.0.26200, Intel i7-1265U, CPU only, Python 3.11.9.

## Clone 1: application (commit 1448d7a)
- Imports resolved inside the clone (`backend/engine.py`, `scripts/smoke_inference.py`, `third_party/LoGoHTR`). The venv has no `.pth` path hooks into the original folder, and `PYTHONPATH` was unset.
- The server started from the clone: `python -X utf8 -m uvicorn backend.app:app --port 8001`, model loaded.
- **Live HTTP check: 16/16** ([CLONE_LIVE_HTTP_CHECK.json](CLONE_LIVE_HTTP_CHECK.json)), covering:
  - health, model info, `/docs` and the OpenAPI schema;
  - recognition in both modes;
  - two-crop verification;
  - the three demo sheets (accept, flag, review), plus the proposed-mode slow path (30.6 s);
  - three error cases;
  - the saved benchmark.
- The OpenAPI schema exported from the clone's live server is byte-identical to the committed `openapi.json`.
- Backend tests inside the clone: **20/20 unit** (mocked inference) and **7/7 integration** (real checkpoint; predictions equal the offline research predictions).

## Problem found and fixed: line endings broke recorded hashes
- **Symptom.** In clone 1, the M7 frozen-hash check failed for 7 files: `athn.py`, `run_method.py`, `smoke_inference.py`, `run_baseline.py`, `score_baseline.py`, `m7_select.py` and `SELECTION_PROTOCOL.md`. Their content was identical; with `core.autocrlf=true`, Git had checked LF files out as CRLF.
- **Wider risk.** On a system without CRLF conversion, the opposite would have happened to the files recorded with CRLF, including the M4 dataset manifests that every runner checks.
- **Fix (commit 9ca5789).** A generated `.gitattributes` pins every tracked text file to the line endings its hash was recorded with: CRLF for 127 listed files, LF for the rest. No file content changed.

## Clone 2: integrity after the fix (commit 9ca5789)
- 1,164 of 1,165 tracked files are byte-identical to the verified working copy. The single difference was `FRONTEND_REQUIREMENTS.md`, which had uncommitted edits at that moment.
- Research suites in the clone, without the checkpoint or any git-ignored data:
  - `test_m4_audit` 27/27;
  - test_m7's own 8 tests pass, including the frozen-config hash check that failed before the fix;
  - test_m8's own 6 tests pass.
- Expected failures, each caused by a missing git-ignored input:
  - `test_m4_online`: 3 (CVL archive cache, raw Hugging Face cheque images);
  - `test_m5_dev`: 2 (checkpoint not copied into clone 2);
  - `test_m6`: 3 (`data/stress/`, `data/diagnostics/`).

  These suites are for research reproduction and are not needed to run the application (SETUP_GUIDE.md, "Research reproduction").

## Absolute paths
No code or configuration refers to the original machine:
- tracked code and documents were searched for the user folder, OneDrive and drive paths;
- the only matches are two historical M3-A evidence logs that record where the first run happened (`artifacts/M3_A/ENVIRONMENT.json`, `artifacts/M3_A/run1_stdout.log`);
- the hard-coded Linux backbone path is upstream's, and `smoke_inference.py` intercepts it.

## Not reproduced here, by design
- The locked test benchmark (M8) was not rerun. Its saved results are checked by `tests/test_m8.py` (7/7 in the original working copy) and by `scripts/verify_reported_numbers.py` (14/14 headline numbers match the saved evidence).
- Raw dataset downloads and stress-set regeneration were not repeated.
