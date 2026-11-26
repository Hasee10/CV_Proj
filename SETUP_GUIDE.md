# Setup guide: running the ChequeVerify backend

This guide covers the application only. You do not need any research dataset to run the backend. The crops and demo sheets the tests use are already in the repository. To reproduce the research tables, see "Research reproduction" at the end.

## What has been tested
| item | tested |
|---|---|
| OS | Windows 11 Pro (10.0.26200), CPU only (Intel i7-1265U) |
| Python | 3.11.9 |
| Fresh clone | yes. The committed repository was cloned into an empty folder, then the server started and all backend tests passed. The upstream code and checkpoint came from local copies, and the Python packages from an existing environment pinned to the same versions. See [artifacts/FINAL_BACKEND_HANDOVER/REPRODUCTION_REPORT.md](artifacts/FINAL_BACKEND_HANDOVER/REPRODUCTION_REPORT.md). |
| Cold install on a new machine | not tested |
| Linux, macOS, GPU | not tested |

## Fast path: one command
After cloning (step 1), run from the repository root:
```powershell
py -3.11 scripts/setup_env.py
```
It carries out steps 2 to 4 and the test part of step 7, and enables the git commit guard (see `CLAUDE.md`). It is safe to rerun and ends with `SETUP COMPLETE`. The manual steps below show what it does.

## 1. Get the code
```powershell
git clone https://github.com/Hasee10/CV_Proj.git ChequeVerify
cd ChequeVerify
```

## 2. Python environment
Python 3.11 is required. The pinned torch 2.15 CPU wheels are not available for every Python version.
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt -r requirements-backend.txt
```
- `requirements-inference.txt` pulls torch from the PyTorch CPU index; the URL is inside the file. Expect a download of several hundred MB.
- `requirements-analysis.txt` (matplotlib) is only needed to redraw research figures.
- On Linux or macOS (untested), create the venv with `python3.11 -m venv .venv` and use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe` throughout.

## 3. Upstream LoGo-HTR code (pinned commit)
```powershell
git clone https://github.com/shreemitra/LoGoHTR third_party/LoGoHTR
git -C third_party/LoGoHTR checkout 9eaea5fe52e908ebf3b625ca4c05da3d1905a6af
```
Keep this folder unmodified. Two missing pieces in the upstream code are bridged at run time by `scripts/smoke_inference.py`:
- a dictionary file the upstream code expects but does not ship;
- a hard-coded backbone path from the authors' machine.

## 4. Checkpoint and its SHA-256
```powershell
New-Item -ItemType Directory -Force models/logo_htr
curl.exe -L -o models/logo_htr/Downstream_Full_Model_Best.ckpt "https://huggingface.co/Shree10/LoGo-HTR/resolve/64439ca9edfbf58e3007c2bb6af17559bcf2d29e/Downstream_Full_Model_Best.ckpt"
(Get-FileHash models/logo_htr/Downstream_Full_Model_Best.ckpt -Algorithm SHA256).Hash
```
The hash must be `25DB3A51F70A08CD5CBBF88409470BC4B37821AFF95BC5EE6AB89E1E4298C432`. The backend checks it at startup and refuses any other file. If the check fails, the server still starts but answers 503 `model_unavailable`.

## 5. Configuration (optional)
All settings are environment variables with working defaults. [.env.example](.env.example) lists them. No secrets are involved. The ones you may need:
- `CV_CORS_ORIGINS`: browser origins allowed to call the API. The default is `http://localhost:5173,http://127.0.0.1:5173` (a Vite dev server).
- `CV_INFERENCE_TIMEOUT_S`: default 120 s.

Set them in the same terminal before starting the server, for example:
```powershell
$env:CV_CORS_ORIGINS = "http://localhost:3000"
```

## 6. Start the backend
```powershell
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Wait for `Application startup complete.` The model loads once; this took a few seconds on the test laptop. Swagger UI is at http://127.0.0.1:8000/docs.

## 7. Smoke tests
With the server running, open a second terminal:
```powershell
curl.exe http://127.0.0.1:8000/health
```
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\m10_live_check.py
```
- `/health` must return `{"status":"ok","model_loaded":true}`.
- The live check sends 16 real requests and expects `16/16 passed`. One request is the deliberately slow proposed-mode written line, about 30–40 s. Results go to `.cache/live_check.json` (git-ignored). No tracked file changes.

Test suites (no server needed):
```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest tests\test_backend_unit.py tests\test_backend_integration.py -q
```
- Expected: 27 passed.
- The 20 unit tests use mocked inference. The 7 integration tests load the real checkpoint. Neither suite changes tracked files.

## Troubleshooting
| symptom | cause and fix |
|---|---|
| `/health` returns 503 | Checkpoint missing or hash mismatch (step 4), or `third_party/LoGoHTR` missing or at the wrong commit (step 3). |
| `ERROR: run with python -X utf8` from a script | Research scripts need UTF-8 mode; keep the `-X utf8` flag. |
| `FileNotFoundError ... IIIT_Dict.txt` | You imported the upstream package directly. Go through `scripts/smoke_inference.py` (as the backend does), which installs the dictionary adapter. |
| Browser shows a CORS error | Add your frontend origin to `CV_CORS_ORIGINS` and restart the server. |
| Requests in `proposed` mode take 30 s or more | Expected for written-amount lines. See the latency section of [HANDOVER.md](HANDOVER.md). Use `mode=baseline` for fast demos. |
| 503 `busy` | One inference slot (`CV_MAX_CONCURRENCY=1`) is still running an earlier, possibly timed-out request. Retry after it finishes. |
| `pip` cannot find `torch==2.15.0+cpu` | Use Python 3.11 and keep the `--extra-index-url` line in `requirements-inference.txt`. |
| Slow file access or locked files | A cloud-synced folder (such as OneDrive) can lock the 900 MB venv or checkpoint. Pause sync or use a local folder. |

## Research reproduction (not needed for the app)
The research results (M4–M8) are committed under `artifacts/`. Regenerating them needs:
- `requirements-analysis.txt`;
- the raw dataset fetch scripts in `scripts/` (`fetch_online_data.py`, `fetch_gnhk_test.py`), as described in [README.md](README.md);
- hours of CPU time.

The research test suites (`tests/test_m4_*.py` to `tests/test_m8.py`) also read regenerated, git-ignored data such as `data/stress/`, so they pass only in a working copy where those steps have been run. Do not rerun the locked test evaluation to tune anything: its results are final.
