# ChequeVerify project tracker

States: VERIFIED, PARTIAL, BLOCKED, NOT STARTED. VERIFIED requires recorded evidence.

| Milestone | State | Evidence / note |
|---|---|---|
| M0 Professor requirements reviewed | VERIFIED | `research/guidlines/` PDF re-read 2026-11-26; matches guidelines.md |
| M1 Paper review (document review, not replication) | VERIFIED | `research/paper2/paper2.md` |
| M2 Paper selection | VERIFIED | LoGo-HTR (Mitra, Mondal, Jawahar, WACV 2026) finalized with documented limitations; ProtoSig dropped; single-paper baseline permitted by the professor |
| M3-A Checkpoint acquisition and CPU inference | VERIFIED (feasibility only) | `artifacts/M3_A/SUMMARY.json`: strict load 673/673 keys, 6,385,537 params, 8/8 preselected in-domain samples decoded exactly, median 0.14 s/word on CPU. Out-of-domain check NOT STARTED (risk R1) |
| M3-B Independent handwriting feasibility | VERIFIED (protocol, not accuracy) | `artifacts/M3_B/SUMMARY.json`: 9 student photos, manifest frozen before inference. Crop 4/9 exact, CER 0.265; numeric 2/5 (digits-only 3/5); punctuation emitted 0/3 (corrected: 0/2 strict, H04 ambiguous excluded); multiword line 0/1 but segmented words 3/3; median 1.11 s per crop on CPU. Recommendation B accepted. Final labels in `artifacts/M3_B_final/` (H05 `75,450.50` writer-confirmed; H04 ambiguous) |
| M4 Dataset preparation and evaluation design | VERIFIED WITH DOCUMENTED LIMITATIONS | `artifacts/M4_FINAL/SUMMARY.json`: manifests frozen (unchanged from M4-ONLINE); 872 entries / 854 unique images (612 genuine, 260 synthetic); 0 true duplicates among 227 candidates (pixel + lineage audit); blank fields excluded from recognition metrics; IDRBT direct ZIP failed (DNS) |
| M5 Baseline evaluation | PARTIAL (dev VERIFIED; locked test pending) | `artifacts/M5_DEV/SUMMARY.json`: 251 dev entries, 0 errors, no test inference. Exact: D1 34/80 (CER 0.305), CVL 38/90 (CER 0.185), synthetic 0/72 (CER 0.87-0.99). Synthetic pairs: all 72 routed to review (no automatic verification). 121.6 s CPU inference, median 0.29 s |
| M6 Stress and failure analysis | VERIFIED | `artifacts/M6/SUMMARY.json`: 3,675 paired stress variants + 302 diagnostic inputs on dev (0 errors, 44.8 min CPU). Severe contrast/blur/noise hurt genuine text; upscaling recovers small synthetic numbers (0/8 -> 5/8) but harms genuine text; line removal does not help; oracle word segmentation helps only with scale. M7 recommendation: adaptive text-height normalisation |
| M7 Improvement | NOT STARTED | |
| M8 Comparative and ablation evaluation | NOT STARTED | |
| M9 Application | NOT STARTED | |
| M10 Reproducibility and testing | NOT STARTED | |
| M11 Report | NOT STARTED | |
| M12 Presentation and demo | NOT STARTED | |

## Decisions log
- 2026-11-26: Instructor permits AI assistance ("external party" = other students), as reported by the student. Disclosed in THIRD_PARTY_NOTICES.md.
- 2026-11-26: Project root is the OneDrive folder (D:\Projects does not exist).
- 2026-11-26: Vocabulary `SSL_HWD_Dict.txt` chosen on decisive empirical evidence (see MODEL_INSPECTION.md §2).
- 2026-11-26: Smoke samples drawn from SSL-HWD (Apache-2.0) by pre-registered rule; student-written samples still pending.
- 2026-11-26: M3-A reviewed by supervisor and passed. M3-B run on student-written photos; inference script hardened (required --out, overwrite guard, per-sample readability check).
- 2026-11-26: Student photos were found in `handwritten_examples/` (root), not `data/handwritten_examples/raw/`; byte-identical copies were made and the originals were left untouched.
- 2026-11-26: M3-B ground-truth correction pass after supervisor visual audit (H04 `1250-00`, separator ambiguous and excluded from strict punctuation; H05 audit reading `75,430.50` adopted as disputed, then reverted to `75,450.50` after the writer confirmed it). Net change: punctuation denominator 3 -> 2; all exact-match and CER figures equal original M3-B. Recommendation B unchanged. See `artifacts/M3_B_corrected/`.

- 2026-11-26: M2 finalized (LoGo-HTR, documented limitations). H05 resolved as `75,450.50` by the writer's confirmation (`artifacts/M3_B_final/`). M4: GNHK chosen (CC-BY-4.0; IAM unreachable and registration-gated); official GNHK page no longer serves data, pinned HF mirror used. Custom data collection pending.
- 2026-11-26: M4-AUDIT: strict numeric/written-amount grammars, parser-independent GT values, failure-aware and label-validated metrics, hardened sheet extraction/finalize, near-duplicate review gate, stress lineage checks; protocols amended (dated). M4 stays PARTIAL.
- 2026-11-26: M4-PILOT attempt 1 BLOCKED: no photo in data/custom/raw/ (W01_A.jpg not found). Three review findings (duplicate-id CSV collapse, non-finite verified_value, Unicode digits) recorded as pending before finalize. See `artifacts/M4_PILOT/`.
- 2026-11-26: M4-ONLINE: student retired manual collection; M4-PILOT superseded (not passed). Online data acquired (CVL genuine numeric, GNHK genuine number words, HF synthetic cheques); three pending audit fixes resolved. M4 VERIFIED under the revised strategy.
- 2026-11-26: M4-FINAL: IDRBT direct ZIP unreachable (DNS); duplicate audit found no true duplicates; CVL writer id confirmed as undocumented (inferred); eligibility rules frozen. M4 VERIFIED WITH DOCUMENTED LIMITATIONS.
- 2026-11-26: M5-DEV: frozen baseline run on dev only (cached by image + config hash); metrics reproducible from saved predictions; synthetic cheque fields fail almost completely (low-resolution font text); test split untouched. M6 needs authorisation.
- 2026-11-26: M6 verified (dev only). Recommended M7 primary contribution: adaptive text-height normalisation; word segmentation conditional; line removal rejected. matplotlib added (requirements-analysis.txt).

Deadlines: 2 Dec 2026 implementation/models/dataset; 3 Dec report; 4 Dec presentation and live demo.
