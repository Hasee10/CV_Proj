# Frontend prompt for the collaborator

Open a fresh Claude Code session in the repository root, paste everything inside the block below as your first message, and let the agent work through milestones F1 to F6. The agent needs no earlier chat history. Review each milestone report before you tell it to continue, and make sure the backend can be started on your machine (checkpoint and upstream code are git-ignored; HANDOVER.md and README.md explain how to fetch them).

````
You are building the frontend for ChequeVerify, an academic prototype that reads handwritten cheque amounts and checks whether the numeric and written amounts agree. The backend and the research results are finished and frozen. You have no earlier conversation to rely on: the repository documents are the source of truth. If this prompt and a document disagree, the code in backend/app.py wins, then API_CONTRACT.md, then FRONTEND_REQUIREMENTS.md. Say so in your report whenever you find such a difference.

## Step 1: read before writing code
1. Read HANDOVER.md, FRONTEND_REQUIREMENTS.md and API_CONTRACT.md completely. Then read SETUP_GUIDE.md and DEMO_GUIDE.md.
2. Inspect backend/app.py, backend/engine.py and openapi.json. Look at every JSON file in artifacts/M10/examples/ and at data/demo/demo_manifest.json. These are real captured responses and real demo inputs.
3. Read CLAUDE.md and PROJECT_TRACKER.md.
4. Never invent an endpoint, form field, response field or status code. If it is not in the code or the examples, it does not exist.

## Step 2: set up the environment, start the backend and confirm it works
Run the one-command setup from the repository root: `py -3.11 scripts/setup_env.py` on Windows (`python3.11 scripts/setup_env.py` elsewhere). It creates .venv, installs the pinned packages, fetches and verifies the upstream code and the checkpoint, enables the commit guard and runs the backend tests. It must end with SETUP COMPLETE; if it does not, report the error and stop. Then start the backend: `.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. Set the environment variable CV_CORS_ORIGINS if your dev server does not run on http://localhost:5173 or http://127.0.0.1:5173. Confirm that GET http://127.0.0.1:8000/health returns 200 with model_loaded true. If it does not, stop and report the cause (usually the git-ignored checkpoint or upstream code is missing). Do not continue with mocks only.

## Step 3: the backend is frozen
- Do not modify anything outside frontend/, except status updates in README.md, PROJECT_TRACKER.md, ROADMAP.md and PROJECT_CONTEXT.md. This is enforced: .claude/settings.json denies edits to frozen paths, the git pre-commit hook (scripts/guard.py --staged) refuses commits that touch them, and `python scripts/guard.py --verify` checks every frozen file against FROZEN_MANIFEST.json. Run the verify command before every commit. Never bypass these checks (no --no-verify, no changes to core.hooksPath, the hook, the manifest or the settings).
- All frontend code goes in a new top-level directory frontend/. Frontend tests go inside frontend/.
- The only backend-side change allowed is setting CV_CORS_ORIGINS through the environment when you start it.
- If you believe the backend has a bug or the API needs a change, do not fix it. Write it in your report and stop that item.
- Do not add backend endpoints. If you need static data (for example confidence intervals), bundle a read-only, byte-identical copy of the repository file into frontend/ at build time, and never edit it.

## What to build
A professional, restrained banking-style UI: neutral palette, one accent colour, plain type, no decorative animation. Use React or Next.js with TypeScript (Vite is fine), and Tailwind or CSS modules. Implement sections A to F of FRONTEND_REQUIREMENTS.md:
- A: Dashboard (readiness from /health and /api/model-info, limitations, navigation).
- B: Cheque verification workspace (upload, preview, draw, edit and reset two boxes, keyboard alternative with numeric inputs, exact conversion from displayed pixels to natural pixels to normalised [x0, y0, x1, y1], mode selector, submit).
- C: Recognition results (raw_text verbatim, parsed_value, parse_status, preprocessing fields that exist, every latency_seconds field including queue_wait).
- D: Verification decision (accept, flag, review as "Amounts agree", "Amounts differ", "Needs human review"; reasons verbatim; notice always visible).
- E: Research benchmark dashboard from /api/benchmark, with genuine and synthetic groups separated, dataset tables (CER, WER, exact, value_exact, baseline against proposed) and pair decision tables (decisions, review rate, decision coverage, incorrect acceptance rate, confusion). Confidence intervals only if you bundle STATISTICAL_ANALYSIS.json unmodified as a static file; otherwise omit them and say so on the page.
- F: UX (responsive from 360 px, honest loading states, no duplicate submissions, accessibility, error-code mapping, model-unavailable state, 503 busy and 504 timeout handling with a manual retry, baseline always available).

Integrate every endpoint: GET /health, GET /api/model-info, POST /api/recognize, POST /api/verify in both input forms (cheque_image with numeric_roi and written_roi, and numeric_image with written_image), and GET /api/benchmark.

Behaviour you must get right:
- Modes are baseline and proposed (ATHN). The default selection comes from default_mode in GET /api/model-info (currently proposed). Baseline is always available. Proposed mode on written-amount lines can take tens of seconds, and some lines exceed the 120 s server timeout. Offer baseline for written-heavy demos.
- A 504 inference_timeout means the server stopped waiting, but the model call cannot be interrupted and keeps its single inference slot until it finishes. Other requests may get 503 busy meanwhile. Cancelling a browser request does not stop server computation. Say this honestly in the UI. Retries are manual, never automatic.
- /api/verify runs two recognitions in sequence, each with its own timeout. Set the client timeout to at least 250 s or none.
- Send the original File unchanged. Do not set the Content-Type header yourself for FormData.
- Decisions: accept means both values parse and are equal; flag means both parse and differ; review means at least one does not parse. Accept is not proof of authenticity. beam_log_probability is not a confidence: omit it or label it "model score (uncalibrated)".
- Synthetic cheque written amounts never parse, so synthetic pairs always end in review.

## Tests you must write and run
1. Unit tests for the ROI conversion: a plain image; a scaled preview (for example 1800 x 1200 natural shown at 600 x 400, drag from (100, 50) to (300, 150) gives [0.166667, 0.125, 0.5, 0.375]); clamping to [0, 1]; reversed drags; the 8 px minimum after scaling; and an EXIF-rotated image where the natural dimensions after orientation are used. Create the EXIF fixture inside frontend/ tests (generate it in the test or add a tiny file there); do not add other images to the repository.
2. Real backend requests using data/demo/sheet_accept.png, data/demo/sheet_flag.png and data/demo/sheet_review.png with the ROIs from data/demo/demo_manifest.json. With mode baseline the expected decisions are accept, flag and review. Label these in code and in the UI as constructed demo inputs, not benchmark evidence. Compare the returned rois pixel boxes with the manifest box_px (allow 1 px rounding).
3. Mocked-fetch tests for loading, 503 busy, 503 model_unavailable, 504 inference_timeout, and the 413, 415 and 422 error codes in the FRONTEND_REQUIREMENTS.md table, including a non-JSON error response and a network failure.
4. Responsiveness (360 px, 768 px, desktop) and accessibility checks: keyboard-only operation of the whole verify flow, labels, contrast, aria-live announcements, and axe or Lighthouse with no critical or serious violations.
5. End-to-end tests (for example Playwright) against the running backend: upload, draw or type boxes, submit in baseline mode, check the decision, reasons, notice and latency display, and check the benchmark page renders genuine and synthetic groups separately. Keep proposed-mode end-to-end tests to short numeric crops or give them a long timeout; do not make them required for the milestone.
Record exact commands and real outputs. Do not claim a test passed if you did not run it.

## Milestones and acceptance criteria
Stop after each milestone, report evidence (commands, test output, screenshots or accessibility reports), then wait for the student to say continue.
- F1 scaffold and health: frontend/ builds, a dev server runs on port 5173, the Dashboard shows live /health and /api/model-info data and the limitations text, the model-unavailable state works when the backend is stopped.
- F2 verification workspace and ROI tests: upload, preview, draw, edit and reset two boxes, numeric-input alternative, mode selector, both verify input forms. ROI unit tests pass. A real baseline request on sheet_accept.png succeeds.
- F3 results and decision display: sections C and D complete, all three demo sheets give accept, flag and review in baseline mode, notice and reasons verbatim, wording rules followed, recognise-one-field page works.
- F4 benchmark dashboard: section E complete with genuine and synthetic separated, numbers identical to /api/benchmark output (spot-check at least five values against the JSON), limitations and static notes present, confidence intervals either bundled unmodified or omitted with an explanation.
- F5 UX, error states and accessibility: loading indicator with elapsed time and no percentage, duplicate-submit protection, every row of the error table handled, 503 busy and 504 handling with manual retry, responsive layout, accessibility checks clean.
- F6 end-to-end, tracker and commit: Playwright suite passes against the live backend, PROJECT_TRACKER.md updated, commit and push done.

## Tracker, commits and pushing
- Update PROJECT_TRACKER.md with two entries: M9-B (frontend) and M10-B (full integration). Use only the states VERIFIED, PARTIAL, BLOCKED or NOT STARTED, and add the evidence (test commands, counts, dates). Do not mark VERIFIED anything you did not run. Leave other tracker rows as they are.
- Commit and push the frontend work only after every check above passes. Use clear messages, one logical change per commit, and end each message with the attribution line the harness gives you.
- Never force-push. Never commit node_modules, build output, .env files, secrets, model weights, or images other than test fixtures that are already in the repository. Check git status before every commit.
- If push fails (for example no remote access), report it and stop; do not work around it.

## Do not
- Do not change research methodology, results, thresholds, the frozen configuration, or any number in artifacts/.
- Do not fabricate, round differently or recompute metrics. Show /api/benchmark values as returned.
- Do not show fake progress bars or percentages. Show an indeterminate indicator with elapsed seconds.
- Do not claim or imply fraud detection, tamper detection, signature verification, authenticity, bank clearing, authentication or accounts. Do not use "verified", "genuine" or "authentic" for an accept decision.
- Do not add backend endpoints, new request fields or new response fields.
- Do not auto-detect fields, auto-correct recognised text, or store images or recognised text anywhere in the browser.
- Do not log raw_text or image data in production builds.
- Do not use real customer cheques. Use only the repository demo sheets and synthetic or consented images.
- Do not run the research scripts or tests, or start training of any kind.

## Report format
At each milestone: what you built, files changed (frontend/ only), commands run with real results, anything that disagreed between code and documents, and anything blocked. Plain English. Stop and wait.
````
