# M6 commands (PowerShell, project root; dev split only)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-analysis.txt          # matplotlib for figures
.\.venv\Scripts\python.exe -X utf8 -I scripts\m6_prepare.py                      # parents, 3,675 stress variants, DX-B/C/D images
.\.venv\Scripts\python.exe -X utf8 -I scripts\m6_dxc_oracle.py                   # DX-C oracle word crops (AI visual boxes)
.\.venv\Scripts\python.exe -X utf8 -I scripts\run_inference_set.py --manifest data\stress\m6_dev\manifest.json --limit-ids data\stress\m6_pilot_ids.json --cache data\stress\m6_cache.jsonl --out artifacts\M6\STRESS_PILOT_RESULTS.json
.\.venv\Scripts\python.exe -X utf8 -I scripts\run_inference_set.py --manifest data\stress\m6_dev\manifest.json --cache data\stress\m6_cache.jsonl --out artifacts\M6\STRESS_RESULTS.json
.\.venv\Scripts\python.exe -X utf8 -I scripts\run_inference_set.py --manifest data\diagnostics\m6\manifest.json --manifest data\diagnostics\m6\dxc_oracle_manifest.json --cache data\diagnostics\m6_cache.jsonl --out artifacts\M6\DIAGNOSTIC_RAW.json
.\.venv\Scripts\python.exe -X utf8 -I scripts\m6_analyze.py                      # metrics, CIs, diagnostics, pairs, figures
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m6.py --out artifacts\M6\TEST_RESULTS.json
```

- The runner refuses non-dev entries, caches by image hash plus the full configuration, and resumes after interruption.
- Every output script refuses to overwrite existing results.
- Seed: 20261126 for corruptions and bootstrap.
- The severity-3 legibility grid (`figures/severity3_legibility_grid.png`) was rendered from the stress manifest by a fixed rule: the first parent per group by sorted id.
