# M4 public dataset selection

## Candidates checked (2026-11-26)
| Dataset | Source checked | Access | Licence | Word-level | Writer ids | Official split | Download | Decision |
|---|---|---|---|---|---|---|---|---|
| **GNHK** (Lee et al., ICDAR 2021) | github.com/GoodNotes/GNHK-dataset (README, licence). The official page goodnotes.com/gnhk now 301-redirects to the Goodnotes homepage | free, no registration | **CC-BY-4.0** (redistribution allowed with attribution) | yes: page photos + JSON quadrilateral polygon per word (`text`, `polygon`, `line_idx`, `type` H/P) | **no** (page id only) | yes: train / test archives | test archive only: 286 MB compressed via HTTP range from a pinned mirror | **SELECTED** |
| **IAM** (Marti & Bunke 2002) | fki.tic.heia-fr.ch/databases/iam-handwriting-database: connection refused (ECONNREFUSED), twice by fetch agent and once by curl | requires registration (known; not re-verified today) | research, non-commercial terms (not re-verified) | yes | yes | Aachen split (external) | ~1.1 GB words archive (not verified) | **not used**: site unreachable, registration needed; unofficial mirrors would bypass access terms |
| SSL-HWD (paper's own) | HF `Shree10/SSL-HWD-Words` | free | Apache-2.0 | yes | writer folders | 60/40 split stated, membership **not published** | 14.5 GB zip | not used as standard benchmark: the checkpoint very likely trained on it (M3-A risk R1) |
| RIMES, LAM | not pursued | registration / French or Italian historical | - | - | - | - | - | out of scope (non-English or line-level) |

## Why GNHK
- It is one of the paper's four benchmarks (Table 3: WER 12.07 / CER 7.20 at 100% labels; authors' numbers, not reproduced).
- Camera-captured handwriting "in the wild", which is closer to phone-photographed cheques than scanned IAM forms.
- A clear permissive licence and no registration. An official test partition exists.
- It contains digits and punctuation (`97/134`, `26/06/12`, `4.`, `1-`), which are relevant to amount fields.

## Provenance caveat
The official download page no longer serves data. The archive was taken from the Hugging Face mirror `staghado/GNHK-Dataset` @ `eaa67d396fd29b8b04e38d630da79f67db11b212` (`GNHK-dataset.zip`, 1,010,143,400 bytes; its size equals the `drive-download-…zip` in the same repo, consistent with a copy of the original Google Drive bundle). No official checksum exists to compare against. Integrity is limited to the inner zip CRC-32 (1897843626) and the recorded SHA-256 of `test_data.zip` (`6f3d65d9…eacb`). The redistribution is permitted by CC-BY-4.0.

## Subset (actual, acquired)
- 172 official test pages, 10,066 annotated words: 9,199 handwritten, 867 printed. 369 `%NA%`/`%SC%`/`%math%` tokens and 1 out-of-vocabulary word were excluded, leaving 8,829 eligible.
- **240 word crops** were selected by the fixed rule in `scripts/build_gnhk_subset.py` (seeded, independent of model output).
  - Page-disjoint split: 52 dev pages and 120 test pages.
  - 80 dev words (20 containing digits, 60 other) and 160 test words (40 digit, 120 other).
  - At most 3 words per page; 122 pages used.
- **Why 240:** it is close to the 200–300 suggestion. 160 test words give a 95% binomial interval half-width of about ±7 percentage points at 70% exact match, and about 1,080 ground-truth characters for CER. At the M3-B latencies (0.3–2 s per word), one full pass plus 15 stress variants takes well under an hour on this CPU.
- **Download:** 286,039,365 bytes (compressed range). The train archive (724 MB) was not downloaded. Crops on disk total 9.0 MB.

## Known limitations
- No writer ids, so the split is page-disjoint, used as a proxy for writers. **Writer-disjointness is not verified.**
- Training overlap: the checkpoint's fine-tuning data is undocumented. The authors also report GNHK fine-tuning (Table 3), so GNHK *training* pages could be in the checkpoint. The official *test* split should be outside any authors' fine-tuning, but this **cannot be guaranteed**.
- Labels are used as published. A spot check found possible annotation noise: `000` shows a leading stroke, and a `1` looks like `x`. These were not relabelled.
- Crops are axis-aligned boxes around the official polygons (annotation or oracle crops), with no margin and no rectification.
- The digit stratum is over-sampled (25% vs about 5–6% natural) on purpose, for domain relevance. Aggregate metrics are therefore not GNHK-representative and must be reported per stratum.
