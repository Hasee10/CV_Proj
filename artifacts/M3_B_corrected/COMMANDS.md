# M3-B correction pass: commands (PowerShell, project root)

No inference was rerun, nothing was downloaded, and nothing was trained. Inputs are the original `artifacts/M3_B/INFERENCE_RESULTS.json` and `artifacts/M3_B/DATA_MANIFEST.json`, both unchanged; their SHA-256 values were re-checked after the pass.

```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\m3b_correct.py
```
This writes `artifacts/M3_B_corrected/INFERENCE_RESULTS.json`, `DATA_MANIFEST.json` and `METRICS.json`. Internally it calls `m3b_metrics.main("M3_B_corrected")`. The script asserts that every prediction, raw token id and latency is identical to the original M3-B run.

The metrics alone can be recomputed with:
```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\m3b_metrics.py M3_B_corrected
```

## Script changes
- New `scripts/m3b_correct.py`, which holds the correction table (H04, H05), the ambiguity notes and the sensitivity analysis.
- Revision 2 (same day): H05 reset to `75,450.50` after the writer confirmed the reading. `m3b_correct.py` was rerun, which regenerated this folder's JSON files; revision 1's `75,430.50` outputs are superseded.
- `scripts/m3b_metrics.py` now takes an artifact folder argument (default `M3_B`, so the original command is unchanged). Rows flagged `punctuation_strict_eligible: false` are left out of the strict punctuation list and listed under `punctuation_excluded_ambiguous`. Original M3-B rows carry no flag, so their output is unchanged.
- `scripts/make_handwritten_crops.py` and `data/handwritten_examples/manifest.json` are deliberately unchanged. They reproduce the original frozen manifest (SHA-256 `d0cd3812…`), and the corrections are applied on top by `m3b_correct.py`.

## Visual inspection performed
Enlarged views of photo 4's separator and photo 5's digits were checked, including a side-by-side of the disputed digit with the writer's other `5` glyphs. These were temporary images in the session scratchpad, not project files, and were not used as model inputs.
