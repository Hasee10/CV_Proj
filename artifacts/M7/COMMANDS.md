# M7 commands (Windows, project root, venv Python 3.11.9)

```powershell
# 1. Freeze the protocol (before any M7 inference)
certutil -hashfile artifacts\M7\SELECTION_PROTOCOL.md SHA256   # recorded in PROTOCOL_FROZEN.sha256
# 2. Dev runs (B0 reused from artifacts/M5_DEV; the cache is seeded from the M5 prediction cache)
bash data/m7/run_all.sh            # P1-A, P1-B, P1-C, P1-D, B1 -> artifacts/M7/dev/<id>/BASELINE_RESULTS.json
#    each line: .venv\Scripts\python.exe -X utf8 -I scripts\run_method.py --split dev --config artifacts\M7\configs\<id>.json --out-dir artifacts\M7\dev\<id> --cache data\m7\cache.jsonl
# 3. Score and select (frozen rules)
.venv\Scripts\python.exe -X utf8 -I scripts\m7_select.py     # scores each run with score_baseline.py --split dev; writes DEVELOPMENT_RESULTS.json
# 4. Conditional segmentation check on the selected config
.venv\Scripts\python.exe -X utf8 -I scripts\m7_p2.py --p1 P1-A   # writes artifacts/M7/dev/P2/P2_RESULTS.json
# 5. Freeze
.venv\Scripts\python.exe -X utf8 -I scripts\m7_freeze.py     # FROZEN_CONFIG.json, ABLATION_RESULTS.json, SUMMARY.json
# 6. Tests (includes the M6, M5 and M4 suites)
.venv\Scripts\python.exe -X utf8 -I tests\test_m7.py --out artifacts\M7\TEST_RESULTS.json
```
Wall time on the i7-1265U CPU: P1-A 1127 s, P1-B 17 s, P1-C 858 s, P1-D 2 s (cache hits), B1 636 s, P2 about 3 min.
