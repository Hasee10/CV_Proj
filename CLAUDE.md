# ChequeVerify: instructions for every Claude Code session in this repository

The project reads the two handwritten amounts on a cheque (in figures and in words) with the frozen LoGo-HTR model, then reports whether they agree. The research (M3–M8) and the FastAPI backend (M9-A, M10-A) are finished and frozen.

**Current stage:** M9-B (build the frontend in `frontend/`) and M10-B (frontend and backend tested end to end). The report (3 Dec) and the presentation with live demo (4 Dec) come after.

Read `HANDOVER.md` first; it links to everything else. The source of truth for the API is `backend/app.py`, then `API_CONTRACT.md`, then `FRONTEND_REQUIREMENTS.md`.

## 1. At the start of every session, before any other work
1. Run `python scripts/guard.py --verify`. Use the venv Python if it exists: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` elsewhere.
2. If `.venv` is missing, `third_party/LoGoHTR` or the checkpoint is missing, or step 1 fails for any reason other than changed frozen files, run the setup:
   - Windows: `py -3.11 scripts/setup_env.py`
   - other systems: `python3.11 scripts/setup_env.py`

   The setup is safe to rerun. It creates the venv, installs the pinned packages, fetches and checks the upstream code and the checkpoint, enables the commit guard, and runs the backend tests. It must end with `SETUP COMPLETE`. If it fails, report the exact error to the user and stop. Do not work around a failed setup.
3. If step 1 reports changed frozen files, restore them with `git restore <path>` before doing anything else, and tell the user which files had changed.
4. To use the API, start the backend with `.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000` and confirm `GET /health` returns `"model_loaded": true`.

## 2. Protected files (enforced, not optional)
You may create, change or delete only:
- anything under `frontend/`;
- `README.md`, `PROJECT_TRACKER.md`, `ROADMAP.md` and `PROJECT_CONTEXT.md`, for status updates only, never to change a reported number.

Everything else is frozen. That includes `backend/`, `scripts/`, `tests/`, `artifacts/`, `data/`, `third_party/`, `models/`, `research/`, every other Markdown document, the requirements files, `openapi.json`, `.gitattributes`, `.githooks/`, `.claude/` and `FROZEN_MANIFEST.json`. Three layers enforce this:
- `.claude/settings.json` denies edits to frozen paths;
- the git pre-commit hook (`scripts/guard.py --staged`) refuses commits that touch them;
- `scripts/guard.py --verify` checks every frozen file against SHA-256 values in `FROZEN_MANIFEST.json`.

Never bypass these layers (`--no-verify`, changing `core.hooksPath`, editing the manifest, the hook or the settings), and never edit frozen files through scripts. If the backend seems to need a change, do not make it: describe the problem and the proposed change to the user and stop that item. The only backend-side setting you may change is the `CV_CORS_ORIGINS` environment variable when you start the server.

## 3. Scientific and honesty rules
- The research results are final. Never rerun or tune anything on the locked test split, and never change the method, model, preprocessing, decoding or any reported number.
- Never fabricate, round differently, cherry-pick or hide results. The frontend shows backend values and the saved benchmark exactly as returned.
- The demo inputs in `data/demo/` are constructed examples, not evidence of accuracy. Label synthetic data as synthetic.
- Claims:
  - `accept` means the two recognised amounts agree. It does not show that a cheque is authentic, and the project does not detect fraud.
  - The beam score is not a confidence.
  - The genuine-handwriting change is not statistically significant. That does not show the two methods are equivalent.
- Use only synthetic or consented images. No real cheques or bank data, and never commit personal photos.
- No paid services, no model training, no other OCR model.

## 4. Working rules
- Frontend code, tests and config live only in `frontend/`. Never commit `node_modules`, build output, `.env` files, weights, archives or files over 5 MB; the guard refuses them.
- Commit only after the relevant tests pass, with clear messages. Never force-push, never rewrite history, never `git reset --hard`.
- Push to GitHub (`origin`, branch `main`) only when the user asks.
- Tracker states are `VERIFIED`, `PARTIAL`, `BLOCKED` and `NOT STARTED`. Report evidence, blockers and decisions, then stop for review.
- Ask before irreversible or expensive actions. No secrets in logs or commits.
- The course instructor allows AI assistance; "external party" in the guidelines means other students. The student team must understand and be able to defend the work. Never present extracted paper text as student writing.
- The course deliverable rules are in `research/guidlines/`, and the paper is `research/paper2/paper2.pdf`. Both are in the private handover archive only, not on GitHub. The PDF is authoritative for the paper's equations and tables.
