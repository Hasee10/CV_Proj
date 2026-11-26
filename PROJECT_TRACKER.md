# ChequeVerify project tracker

States: VERIFIED, PARTIAL, BLOCKED, NOT STARTED. VERIFIED requires recorded evidence.

| Milestone | State | Evidence / note |
|---|---|---|
| M0 Professor requirements reviewed | VERIFIED | `research/guidlines/` PDF re-read 2026-11-26; matches guidelines.md |
| M1 Paper review (document review, not replication) | VERIFIED | `research/paper2/paper2.md` |
| M2 Paper selection | VERIFIED | LoGo-HTR (Mitra, Mondal, Jawahar, WACV 2026) finalized with documented limitations; ProtoSig dropped; single-paper baseline permitted by the professor |
| M3-A Checkpoint acquisition and CPU inference | VERIFIED (feasibility only) | `artifacts/M3_A/SUMMARY.json`: strict load 673/673 keys, 6,385,537 params, 8/8 preselected in-domain samples decoded exactly, median 0.14 s/word on CPU. Out-of-domain check NOT STARTED (risk R1) |
| M3-B Independent handwriting feasibility | VERIFIED (protocol, not accuracy) | `artifacts/M3_B/SUMMARY.json`: 9 student photos, manifest frozen before inference. Crop 4/9 exact, CER 0.265; numeric 2/5 (digits-only 3/5); punctuation emitted 0/3 (corrected: 0/2 strict, H04 ambiguous excluded); multiword line 0/1 but segmented words 3/3; median 1.11 s per crop on CPU. Recommendation B accepted. Final labels in `artifacts/M3_B_final/` (H05 `75,450.50` writer-confirmed; H04 ambiguous) |
| M4 Dataset preparation and evaluation design | VERIFIED (revised strategy, documented limitations) | `artifacts/M4_ONLINE/SUMMARY.json`: custom collection retired; GNHK subset (240) kept; acquired GENUINE CVL digit strings (300, 30 writers, writer-disjoint) and GNHK number-word pairs (72 crops / 54 constructed pairs), and SYNTHETIC cheques (130 cheques, 260 crops, 236 pairs incl. 14 natural mismatches). 872 samples validated; 38/38 tests. No genuine handwritten cheque data obtainable (IDRBT unreachable, ORAND gated) |
| M5 Baseline evaluation | NOT STARTED | |
| M6 Stress and failure analysis | NOT STARTED | |
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

Deadlines: 2 Dec 2026 implementation/models/dataset; 3 Dec report; 4 Dec presentation and live demo.
