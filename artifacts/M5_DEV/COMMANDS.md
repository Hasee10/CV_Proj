# M5-DEV commands (PowerShell, project root)

```powershell
# runtime pilot: first 5 dev entries per dataset by sorted id (fixed rule)
.\.venv\Scripts\python.exe -X utf8 -I scripts\run_baseline.py --out-dir artifacts\M5_DEV --pilot 5
# full dev run (reuses cached pilot predictions with an identical configuration key)
.\.venv\Scripts\python.exe -X utf8 -I scripts\run_baseline.py --out-dir artifacts\M5_DEV
# scoring from saved predictions only
.\.venv\Scripts\python.exe -X utf8 -I scripts\score_baseline.py --dir artifacts\M5_DEV
# sanity tests (+ M4 online and audit suites)
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m5_dev.py --out artifacts\M5_DEV\TEST_RESULTS.json
```

- Cache key = SHA-256 of (image hash, checkpoint hash, preprocessing string, decoding string, dictionary).
- The runner refuses the locked test split unless `--authorize-test-split` is passed. It was **not** used.
- The scripts refuse to overwrite existing results files.
