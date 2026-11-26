# M4 commands (PowerShell, project root; existing `.venv`, nothing reinstalled)

```powershell
# M3-B final labels (H05 writer-confirmed) - writes artifacts/M3_B_final/, refuses to overwrite
.\.venv\Scripts\python.exe -X utf8 -I scripts\m3b_correct.py M3_B_final

# D1 GNHK: fetch only the official test archive (286 MB range, CRC-verified), then the fixed subset
.\.venv\Scripts\python.exe -I scripts\fetch_gnhk_test.py
.\.venv\Scripts\python.exe -X utf8 -I scripts\build_gnhk_subset.py
.\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\public\gnhk\subset\manifest.json --out artifacts\M4\VALIDATION_GNHK.json

# Frozen metric, stress and sheet code: self-tests
.\.venv\Scripts\python.exe -X utf8 -I scripts\eval_metrics.py
.\.venv\Scripts\python.exe -I scripts\stress_corrupt.py --selftest
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py selftest

# D2 collection kit (sheets, amount list, layout)
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py make
# after photos exist (student): extract -> verify annotation.csv by hand -> finalize -> validate
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py finalize
.\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\custom\manifest.json --out artifacts\M4\VALIDATION_CUSTOM.json

# M6 only (not run in M4): paired stress variants into a new empty folder
# .\.venv\Scripts\python.exe -I scripts\stress_corrupt.py data\public\gnhk\subset\manifest.json --split dev --out-dir data\stress\gnhk_dev
```

## Recorded hashes
| File | SHA-256 |
|---|---|
| `data/public/gnhk/cache/test_data.zip` | `6f3d65d91535d1665050afd83a9f3831394d80accfae88c5b91bbb990781eacb` (285,995,725 bytes, CRC-32 1897843626) |
| `data/public/gnhk/subset/manifest.json` | `13450762dd5508154fe05878554d4867d7df94e9a30a614f2b80385371c0af56` |
| `data/custom/template/amount_list.csv` | `e9d86b66135d70a61b0929a5507910b0b46d8d60c7e849cc81dfd2f2686a8335` |
| `data/custom/template/collection_sheets.pdf` | `8b63fe36c62f2d180c634254d5ad9e56037646f96aff1032ea1cef10e6b2a780` |
| `data/custom/template/layout.json` | `ffe92414009f7177fbbbfbc5bce880b013cb8ba35a3e97f193c87fb9454c0a6a` |

## Script changes in M4
- `smoke_inference.py`: per-sample SHA-256 check against the manifest (`input_hash_checked` count in the output).
- `m3b_correct.py`: output folder argument, overwrite refusal and `label_status` provenance. The output is unchanged for the existing folders (all of their hashes were re-verified).
- New: `fetch_gnhk_test.py`, `build_gnhk_subset.py`, `validate_manifest.py`, `eval_metrics.py`, `stress_corrupt.py`, `custom_sheets.py`.
- No inference was run in M4.
