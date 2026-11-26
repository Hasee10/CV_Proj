# M3-A blockers, risks and decisions

## Resolved during M3-A
| # | Issue | Resolution | Evidence |
|---|---|---|---|
| B1 | `C:\Program Files\Git` HTTPS clone blocked by Windows Application Control (`libcurl-4.dll`) | Used the WinGet MinGit binary | COMMANDS.md §1 |
| B2 | `D:\Projects\ChequeVerify` does not exist (only drive C:) | Used the actual project root, as PROJECT_CONTEXT.md allows | ENVIRONMENT.json |
| B3 | Upstream `vocab.py` defaults to `IIIT_Dict.txt`, which is not shipped, so import fails | Runtime adapter outside upstream (MODEL_INSPECTION.md §6.1) | `smoke_inference.py:install_vocab` |
| B4 | Two shipped dictionaries both give the checkpoint's 97 tokens, with different lowercase ordering | Raw ids decoded with both. Only `SSL_HWD_Dict.txt` gives meaningful text (8/8 vs 0/5 lowercase-containing samples) | INFERENCE_RESULTS.json `prediction_by_dict` |
| B5 | Encoder hard-loads a Linux-only backbone path during construction | Construction-time skip of that single load; strict full-checkpoint load (0 missing keys) replaces all weights | MODEL_INSPECTION.md §6.2 |
| B6 | Upstream pins (PL 1.4.9 era) have no Python 3.11 wheels | Current CPU builds; model and decode paths run unchanged; deviation recorded | requirements-inference.txt |
| B7 | Lightning checkpoint holds a `ModelCheckpoint` class reference, which `weights_only=True` rejects by default | Allowlisted only that class via `safe_globals`; the static pickle scan shows nothing else | CHECKPOINT_MANIFEST.json |

## Open risks (not blockers for M3-A; they matter for M2 and later)
| # | Risk | Why it matters | Suggested next action |
|---|---|---|---|
| R1 | **Possible train/test overlap.** All 8 samples are from SSL-HWD `writer1`. The authors' 60/40 split membership is not published, so these images may have been in the checkpoint's training data. | 8/8 exact may reflect memorisation and says nothing about generalisation | Run 5-10 student-written, photographed words and amounts (out of domain, consented) before final paper commitment |
| R2 | No cheque-domain or out-of-domain samples tested | Bank amount fields (printed boxes, `Rs.`, `/-`, commas, decimals, `Only`) are untested | Part of M4/M6 (not M3-A); the R1 check gives an early signal |
| R3 | Punctuation and symbols (`, . / - ₹`) never emitted in this test | Amount strings like `12,500.00` or `₹1,250/-` need them | Include such samples in the R1 check |
| R4 | Vocabulary choice confirmed empirically, not by the authors | Small residual uncertainty for untested ids | Optionally open a GitHub issue asking the authors to confirm; record the answer |
| R5 | Checkpoint's fine-tuning dataset undocumented | Affects how benchmark claims can be phrased | State "undocumented" in the report |
| R6 | Dataset-to-`data.zip` conversion (polarity, JPEG re-encode) not published | Preprocessing is faithful to the code but may differ from the authors' data pipeline | Keep as a stated assumption |
| R7 | Project lives in a OneDrive-synced folder | 929 MB `.venv` and checkpoint sync to the cloud; possible file locks | Student may pause sync or move the folder |
| R8 | Only 8 samples, fixed by rule; the "alphanumeric mixed" rule found 0 images in the fetched bytes | Feasibility evidence only, not an accuracy estimate | No action in M3-A (reported, not replaced) |

## Decisions made (for student review)
- AI assistance: the student reports (2026-11-26) that the instructor permits AI-driven work and that "external party" means other students. Recorded and disclosed in THIRD_PARTY_NOTICES.md.
- Samples: the student did not answer the sample-source question, so licence-checked public samples were used by default (SSL-HWD, Apache-2.0). Student-written samples remain recommended (R1).
- Encoder-only `DenseNet_backbone_step290000.pth` was not downloaded (not needed).
