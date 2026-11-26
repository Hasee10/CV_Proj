# M3-B ground-truth correction log (final)

| Version | Folder | H04 GT | H05 GT | Status |
|---|---|---|---|---|
| Original (frozen before inference) | `artifacts/M3_B/` | `1250.00` (flagged ambiguous) | `75,450.50` | preserved, unchanged |
| Correction rev. 1 | `artifacts/M3_B_corrected/` (overwritten in place by rev. 2; contents not retained) | `1250-00`, alt `1250.00` | `75,430.50` (audit reading; disputed) | superseded |
| Correction rev. 2 | `artifacts/M3_B_corrected/` | `1250-00`, alt `1250.00` | `75,450.50` | preserved, unchanged |
| **Final** | `artifacts/M3_B_final/` | `1250-00`, alt `1250.00`; **ambiguous** | `75,450.50`; **writer-confirmed** | authoritative |

- H05: a visual audit proposed `75,430.50`. The **original writer confirmed `75,450.50`** (2026-11-26), which resolves the disagreement. It matches the original M3-B transcription and the side-by-side glyph comparison.
- H04: the separator is still visually ambiguous (`.` or `-`). Both readings are kept and scored, and the separator is excluded from strict punctuation evaluation. Edit distance is 1 under either reading, so no aggregate depends on it.
- All other labels are visual readings confirmed by the supervisor audit (`label_status` field in `DATA_MANIFEST.json`).
- Predictions, raw token ids, latencies and checkpoint details are the original M3-B values. `scripts/m3b_correct.py` asserts this.
- Revision 1's files were overwritten in place during the earlier correction pass. They are recoverable only by rerunning the rev. 1 correction table, which is recorded above. They were not kept as a separate folder.
