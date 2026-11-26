# M4-AUDIT commands (PowerShell, project root)

```powershell
# full regression suite (27 tests; temporary fixtures only); writes a new results file, refuses to overwrite
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m4_audit.py --out artifacts\M4_AUDIT\TEST_RESULTS.json
# same suite without a results file
.\.venv\Scripts\python.exe -X utf8 -I scripts\eval_metrics.py

# existing self-tests (also run inside the suite)
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py selftest
.\.venv\Scripts\python.exe -I scripts\stress_corrupt.py --selftest

# GNHK subset re-validation with the stricter validator (new report path)
.\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\public\gnhk\subset\manifest.json --out artifacts\M4_AUDIT\VALIDATION_GNHK.json
```

## W01_A pilot (student)
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract --only W01_A
```
Steps are in `artifacts/M4/COLLECTION_INSTRUCTIONS.md` (amendment M4-AUDIT).

## Run record (2026-11-26)
- Suite: 27/27 passed (`TEST_RESULTS.json`).
- GNHK validation: passed, 240 samples, 0 errors, 0 near-duplicate candidates.
- A second validation to the same `--out` was refused (exit 2), as intended.
- No LoGo-HTR inference was run.
