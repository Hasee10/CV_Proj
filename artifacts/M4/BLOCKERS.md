# M4 blockers and limitations

## Blocking M4 = VERIFIED
| # | Blocker | Owner | Resolution |
|---|---|---|---|
| B1 | **Custom banking-domain data not collected** (0 writers, 0 photos) | student + 4–6 volunteers | follow `COLLECTION_INSTRUCTIONS.md`; about 20 min per writer plus about 1–2 h verification |
| B2 | Custom ground-truth verification and split not done (depends on B1) | student | `custom_sheets.py extract`, manual verification, then `finalize` and `validate_manifest.py` |

## Resolved or worked around
| # | Issue | Handling |
|---|---|---|
| R1 | Official GNHK page (goodnotes.com/gnhk) redirects to the Goodnotes homepage | pinned CC-BY-4.0 Hugging Face mirror; provenance and checksums recorded (`DATASET_SELECTION.md`) |
| R2 | IAM site unreachable (ECONNREFUSED) and registration-gated | not used; unofficial mirrors not used, to respect access terms |
| R3 | GNHK polygons are in EXIF-rotated coordinates (29 test pages) | `exif_transpose` before cropping; checked visually |
| R4 | Audit A (no input-hash check) | `smoke_inference.py` now rejects inputs whose SHA-256 differs from the manifest (per-sample error) |
| R5 | Audits B/C (failed rows break metrics or are excluded) | `eval_metrics.text_metrics`: failure-aware primary (empty prediction), success-only secondary, coverage reported. The legacy `m3b_metrics.py` is kept only for M3-B reproduction |
| R6 | Audit D (punctuation by token counting) | alignment-based punctuation precision and recall in `eval_metrics.py` |
| R7 | H05 label dispute | resolved by the writer's confirmation (`75,450.50`); `artifacts/M3_B_final/` |

## Limitations carried forward
- Checkpoint fine-tuning data is unknown, so training/evaluation overlap cannot be ruled out for any set (including the GNHK test split).
- GNHK has no writer ids. Its split is page-disjoint; writer-disjointness is not verified.
- GNHK labels are used as published; possible annotation noise was spotted in 2 crops.
- The GNHK digit stratum is over-sampled; report per stratum.
- M3-A showed checkpoint feasibility only. M3-B was exploratory: 9 samples from 1 writer, with 21 entries being conditions or derived crops of those 9.
- Manual (M3-B) and annotation (GNHK) crops are oracle crops. Custom crops are template-registered. None of these is automatic segmentation.
- The model has never emitted the space token (id 3 → `""`). Multiword recognition is an observed limitation, and the raw output is never space-corrected.
- H04 (M3-B) remains ambiguous (`1250-00` or `1250.00`).
- The paper's published benchmark scores have not been reproduced. M5 will report our own GNHK-subset numbers, which are not comparable to Table 3, a full test set with possibly different preprocessing.
- The project is in a OneDrive-synced folder. The GNHK cache (286 MB) adds to the sync load and can be deleted, since it is re-fetchable and verified by SHA-256.
- Scope: handwritten amount verification only. Signature and forgery detection from the approved topic description are out of scope unless authorised.
