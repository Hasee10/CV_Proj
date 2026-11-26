# Ground-truth review (2026-11-26, supervisor visual audit)

`manifest.json` in this folder is the original M3-B manifest, frozen before inference (SHA-256 `d0cd3812…`), and is kept unchanged. The reviewed ground truth is in `artifacts/M3_B_corrected/DATA_MANIFEST.json`, applied by `scripts/m3b_correct.py`.

| Sample | Was | Final | Note |
|---|---|---|---|
| H04 (`sample_example4.jpeg`) | `1250.00` | `1250-00`, alternative `1250.00` | Separator ambiguous; excluded from strict punctuation evaluation |
| H05 (`sample_example5.jpeg`) | `75,450.50` | `75,450.50` | Audit proposed `75,430.50`; the writer confirmed `75,450.50` (matches the writer's other `5` glyphs) |

Confirmed unchanged: `2500`, `12500`, `50000`, `Twenty`, `Thousand`, `Rupees`, `Five thousand only` (narrow gap after `Five`).
