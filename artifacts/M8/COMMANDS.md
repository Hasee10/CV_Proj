# M8 commands (locked test split; run once after the M7 freeze, commit f836129)

```powershell
# configs: artifacts\M8\configs\B0.json (baseline) and proposed_P1-A.json (byte-identical copy of artifacts\M7\configs\P1-A.json)
bash data/m8/run_test.sh
#  = .venv\Scripts\python.exe -X utf8 -I scripts\run_method.py --split test --authorize-test-split --config artifacts\M8\configs\B0.json --out-dir artifacts\M8\runs\baseline --cache data\m8\cache.jsonl
#  + the same with configs\proposed_P1-A.json --out-dir artifacts\M8\runs\proposed (identity-path crops reuse the baseline cache entries)
.venv\Scripts\python.exe -X utf8 -I scripts\score_baseline.py --dir artifacts\M8\runs\baseline --split test
.venv\Scripts\python.exe -X utf8 -I scripts\score_baseline.py --dir artifacts\M8\runs\proposed --split test
.venv\Scripts\python.exe -X utf8 -I scripts\m8_compare.py      # COMPARATIVE_METRICS, STATISTICAL_ANALYSIS, RUNTIME_REPORT, figures\
.venv\Scripts\python.exe -X utf8 -I tests\test_m8.py --out artifacts\M8\TEST_RESULTS.json
```
Wall time: baseline 243 s; proposed 3,115 s (285 new inferences); comparison with a 10,000-resample bootstrap about 1 min.
