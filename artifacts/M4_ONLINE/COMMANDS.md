# M4-ONLINE commands (PowerShell, project root; existing .venv, no new dependencies)

```powershell
# 1. fetch (CVL 15.8 MB, MD5-checked; synthetic cheques 130 images via the HF rows API). GNHK is already cached (M4).
.\.venv\Scripts\python.exe -X utf8 -I scripts\fetch_online_data.py cvl
.\.venv\Scripts\python.exe -X utf8 -I scripts\fetch_online_data.py hf
# 2. build D4/D5/D6 crops, manifests and amount_pairs.json (refuses to overwrite existing manifests)
.\.venv\Scripts\python.exe -X utf8 -I scripts\build_online_benchmarks.py
# 3. rule-based review of cross-split duplicate candidates (automated, not human)
.\.venv\Scripts\python.exe -I scripts\review_duplicates.py data\benchmarks\duplicate_review.json data\public\gnhk\subset\manifest.json data\benchmarks\cvl_numeric\manifest.json data\benchmarks\gnhk_pairs\manifest.json data\benchmarks\syn_cheques\manifest.json
# 4. joint validation of all 4 manifests plus pair checks
.\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\public\gnhk\subset\manifest.json data\benchmarks\cvl_numeric\manifest.json data\benchmarks\gnhk_pairs\manifest.json data\benchmarks\syn_cheques\manifest.json --resolved data\benchmarks\duplicate_review.json --pairs data\benchmarks\amount_pairs.json --out artifacts\M4_ONLINE\VALIDATION_REPORT.json
# 5. contact sheet and tests (the M4-ONLINE suite also runs the 27-test M4-AUDIT suite)
.\.venv\Scripts\python.exe -X utf8 -I scripts\m4_online_contact_sheet.py artifacts\M4_ONLINE\CONTACT_SHEET.png
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m4_online.py --out artifacts\M4_ONLINE\TEST_RESULTS.json
```

## Recorded hashes (SHA-256)
| File | Hash |
|---|---|
| `data/public/cvl/cache/cvl-strings-train.zip` | `a51b98570afc33dff7e46df830f6b146ac936f8f6680ad0586bc7d3930c3a325` (MD5 `123167109ed2ef554913bd0a9f4d74ba`) |
| `data/benchmarks/cvl_numeric/manifest.json` | `1a98f00bd7e399e6c180d56b741dcc70c1b202cc36576600c2621d83e98e0db8` |
| `data/benchmarks/gnhk_pairs/manifest.json` | `212621826eac3a7ff0c465819ceb530438036e380b6e1f3108425150b7df9dfe` |
| `data/benchmarks/syn_cheques/manifest.json` | `ca62710efe8446d104ff56a65155d2d79ead46b0c86f1b7d70c6d03f980e7226` |
| `data/benchmarks/amount_pairs.json` | `07522b2a95fd76c88b7bc038d6ca0138c8fac255db4a0a2ae7f71ea8457618eb` |
| `data/benchmarks/duplicate_review.json` | `56ee59b4d471522f91e834addb367bb5d2dac72ed272b08704bc8ef815d9d7b3` |
| `data/public/gnhk/subset/manifest.json` | `13450762dd5508154fe05878554d4867d7df94e9a30a614f2b80385371c0af56` (unchanged) |

## Notes
- The synthetic template boxes were refined 4 times by visual review of every crop **before** freezing. The intermediate `data/benchmarks` outputs were deleted and rebuilt; none had been validated, frozen or used.
- No inference, training or manual annotation was performed.
