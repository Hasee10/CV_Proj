# M3-B reproduction commands (PowerShell, project root)

Reuses the M3-A venv, upstream commit `9eaea5f`, checkpoint (SHA-256 `25db3a51…c432`) and `SSL_HWD_Dict.txt`. Nothing was installed or downloaded.

1. Copy the student's photos into `raw/` (originals stay in `handwritten_examples/`, unchanged):
```powershell
New-Item -ItemType Directory -Force data/handwritten_examples/raw, data/handwritten_examples/crops
Copy-Item handwritten_examples/*.jpeg data/handwritten_examples/raw/
```
2. Create the neutral crops and the manifest. The crop boxes and ground truth are fixed in the script and were chosen by visual inspection before inference:
```powershell
.\.venv\Scripts\python.exe -I scripts\make_handwritten_crops.py
Get-FileHash data/handwritten_examples/manifest.json -Algorithm SHA256
```
Frozen manifest SHA-256: `d0cd3812773852128a549963777c9e3c26805d5c32cc34cc2a5c8147764296df`, recorded at 2026-11-26T17:02:40+05:00, before inference (`MANIFEST_FROZEN.sha256`).

3. Baseline inference on all 21 entries (9 crops, 9 full photos, 3 segmented words). `--out` must be a new file:
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\smoke_inference.py --manifest data\handwritten_examples\manifest.json --out artifacts\M3_B\INFERENCE_RESULTS.json
```
The saved log filters upstream's per-parameter "Un-Frozen" lines (`run_stdout.log`).

4. Aggregates:
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\m3b_metrics.py
```
This writes `artifacts/M3_B/METRICS.json`.

## Changes to `scripts/smoke_inference.py` after M3-A (audit findings)
- `--out` is now required, and the script refuses to overwrite an existing file. Verified: pointing it at `artifacts/M3_A/INFERENCE_RESULTS.json` prints a refusal and writes nothing.
- Every input is checked with a PIL verify step before inference. An unreadable image becomes a per-sample error. The warm-up uses the first readable image, and a warm-up failure is recorded, not fatal. Self-check: a corrupt file placed first was reported and the next image still decoded (`2500`). The test output went to the scratchpad, not the evidence folders.
- Per-sample character edit distance (with an assert self-test), CER, `space_token_emitted`, and a labelled `view_space_token_as_space` field were added.
- Model loading, preprocessing, decoding and the vocabulary are unchanged. M3-A artifacts still match their recorded SHA-256 values. M3-A outputs were produced by the earlier version of the script; the changes do not affect predictions.
