# M3-A reproduction commands (Windows PowerShell, from the project root)

Commands were run on 2026-11-26. `git` from `C:\Program Files\Git` could not clone over HTTPS on this machine: Application Control blocked `libcurl-4.dll`. The WinGet MinGit binary worked.

## 1. Upstream code (pinned commit)
```powershell
$git = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd\git.exe"
& $git clone https://github.com/shreemitra/LoGoHTR third_party/LoGoHTR
& $git -C third_party/LoGoHTR checkout 9eaea5fe52e908ebf3b625ca4c05da3d1905a6af
```

## 2. Isolated environment (CPU only)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
```
The original install, before the lock existed, was `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`, then `pip install "pytorch-lightning>=2,<3" torchmetrics einops==0.3.0 opencv-python-headless numpy pillow`.

## 3. Checkpoint (pinned revision) and integrity check
```powershell
New-Item -ItemType Directory -Force models/logo_htr
curl.exe -sSL -o models/logo_htr/Downstream_Full_Model_Best.ckpt "https://huggingface.co/Shree10/LoGo-HTR/resolve/64439ca9edfbf58e3007c2bb6af17559bcf2d29e/Downstream_Full_Model_Best.ckpt"
Get-FileHash models/logo_htr/Downstream_Full_Model_Best.ckpt -Algorithm SHA256
```
Expected: `25DB3A51F70A08CD5CBBF88409470BC4B37821AFF95BC5EE6AB89E1E4298C432`, 52,019,943 bytes. `smoke_inference.py` re-checks the hash before loading.

## 4. Smoke samples (first 4 MiB of the labelled SSL-HWD zip only, rule-based selection)
```powershell
.\.venv\Scripts\python.exe -I scripts\fetch_ssl_hwd_samples.py
```
This writes `data/smoke_samples/ssl_hwd/*.png` and `manifest.json` with SHA-256 hashes. The selection rule is fixed in the script.

## 5. Smoke inference
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\smoke_inference.py --manifest data\smoke_samples\ssl_hwd\manifest.json
```
This writes `artifacts/M3_A/INFERENCE_RESULTS.json`. Run 2 used `--out artifacts/M3_A/INFERENCE_RESULTS_run2.json`. Upstream prints one "Un-Frozen: ..." line per encoder parameter; the saved logs filter those lines with `grep -v "Un-Frozen"`.

Single image: `.\.venv\Scripts\python.exe -X utf8 -I scripts\smoke_inference.py path\to\word.png --out artifacts\M3_A\adhoc.json`

`-X utf8` is mandatory: without it the script exits with code 2. `-I` keeps the current directory off `sys.path`.
