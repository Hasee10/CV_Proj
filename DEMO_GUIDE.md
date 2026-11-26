# Demo guide

A script for showing the backend live, using only inputs already in the repository. Every expected response below was measured, either by `scripts/m10_live_check.py` against a server started from a fresh clone ([artifacts/FINAL_BACKEND_HANDOVER/CLONE_LIVE_HTTP_CHECK.json](artifacts/FINAL_BACKEND_HANDOVER/CLONE_LIVE_HTTP_CHECK.json)) or by the integration tests ([artifacts/M10/examples/](artifacts/M10/examples/)). Times are from a CPU laptop (i7-1265U) and will differ on other machines.

These examples were picked to show each decision type. They are not a sample of benchmark accuracy; for accuracy, show the research results (step 6). All inputs come from the dev split, never the locked test split.

## 1. Start and check readiness
```powershell
.\.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
- Wait for `Application startup complete.`
- `GET /health` should return `{"status":"ok","model_loaded":true}`.
- `GET /api/model-info` shows the checkpoint hash `25db3a51…`, 6,385,537 parameters and `default_mode: proposed`.
- Swagger UI at http://127.0.0.1:8000/docs can run every request below from the browser.

## 2. Single-field recognition (`POST /api/recognize`)
| input (dev split) | field_type | mode | raw_text | parsed_value | time |
|---|---|---|---|---|---|
| `data/benchmarks/syn_cheques/SYN_0001_num.png` (SYNTHETIC, label 3083) | numeric | baseline | `3003` | `3003.00` (wrong) | 0.10 s |
| same image | numeric | proposed | `3083` | `3083.00` (correct) | 0.30 s |
| `data/benchmarks/gnhk_pairs/GNHKP_eng_EU_117_w051.png` (genuine, label "one") | written | proposed | `one` | `1.00` | 0.14 s |

The first two rows show what ATHN does. The synthetic text is about 16 px tall; ATHN enlarges it about 3× (`preprocessing.scale` 3.038) and the reading becomes correct. Say that this is one synthetic example. On the locked test split, ATHN gets 17 of 77 synthetic numeric amounts right, against 0 for the baseline.

## 3. Two-crop verification (`POST /api/verify`)
Inputs: `numeric_image` = `data/benchmarks/gnhk_pairs/GNHKP_eng_EU_310_w021.png` (genuine "1"), `written_image` = `GNHKP_eng_EU_117_w051.png` (genuine "one"). The two crops come from different GNHK pages, so this is a constructed pair.

Response: `decision: accept`, `reasons: ["values_agree: recognised numeric and written values are equal"]`, in 0.17 s. Read out the `notice` text: agreement of the two values is not proof that a cheque is authentic.

## 4. Full-image verification with user-drawn boxes
The three sheets in `data/demo/` are white pages with one numeric crop and one written crop pasted on. They are composites, not cheques. `data/demo/demo_manifest.json` gives each sheet's exact ROIs and sources. Send `cheque_image` plus `numeric_roi` and `written_roi` as JSON strings.

| sheet | content | mode | numeric → value | written → value | decision | reasons | time |
|---|---|---|---|---|---|---|---|
| `sheet_accept.png` | genuine 1 / "one" | baseline | `1` → 1.00 | `one` → 1.00 | accept | values_agree | 0.17 s |
| `sheet_flag.png` | genuine 25000 / "one" (constructed mismatch) | baseline | `25000` → 25000.00 | `one` → 1.00 | flag | values_disagree: numeric 25000.00 != written 1.00 | 0.27 s |
| `sheet_review.png` | SYNTHETIC 3083 / "Three Thousand and Eighty Three" | baseline | `3003` → 3003.00 | `mummisessing` → null | review | written_amount_unparseable | 0.59 s |
| `sheet_review.png` | same | proposed | `3083` → 3083.00 | `mesinomantamentinting` → null | review | written_amount_unparseable | 30.6 s |

How to present the review rows:
- `review` is the safe outcome. The system could not read the written amount, so it does not decide. Every synthetic test pair ends this way with both methods.
- The proposed-mode row fixes the numeric reading but takes about 30 s, because ATHN enlarges the written line to the model's maximum width and the decoder runs long.

ROI example for `sheet_flag.png` (900×291 px), copied from the manifest:
- `numeric_roi` = `[0.727778, 0.137457, 0.955556, 0.32646]`
- `written_roi` = `[0.044444, 0.463918, 0.301111, 0.725086]`

## 5. Error handling (optional)
| request | status | `error.code` |
|---|---|---|
| upload a GIF | 415 | `unsupported_media_type` |
| ROI `[0.9, 0.1, 0.2, 0.3]` (x0 > x1) | 422 | `invalid_roi` |
| `field_type=cheque` | 422 | `invalid_parameter` |

## 6. Research results (`GET /api/benchmark`)
This returns the saved locked-test comparison and is never recomputed. Points to make, all from [artifacts/M8/FINAL_EVALUATION_REPORT.md](artifacts/M8/FINAL_EVALUATION_REPORT.md):
- Synthetic numeric amounts: CER 1.014 → 0.599. Correct values 0/77 → 17/77.
- GNHK words: CER 0.296 → 0.252, exact 73/160 → 78/160.
- CVL digits: CER 0.141 → 0.143, exact 97/210 in both.
- All genuine handwriting: CER change −0.015, 95% CI [−0.036, 0.002]. The interval includes zero, so no significant gain or harm was found. That is not evidence that the two methods are equivalent.
- GNHK amount pairs: automatic decisions 24/52 → 27/52, no mismatch accepted. Synthetic pairs: all review, because no synthetic written amount was read correctly.
- Keep genuine and synthetic numbers apart when presenting.

## Latency rules for a live audience
- Baseline mode answers in well under a second per crop.
- Proposed mode is quick for numeric crops but can take 10–48 s on enlarged written lines. On the test split 5 of 89 such lines took over 120 s; the longest took 419 s.
- After a 504 the model call keeps running and holds the single inference slot. Wait for it to finish before the next request, or restart the server.
- For a smooth demo, show the ATHN effect with a numeric crop (step 2), and run full verifications in baseline mode. Run the slow proposed-mode row once, announced in advance, if you want to show the limitation.

## Do not
- Do not use real cheques or anyone's banking details.
- Do not present the composite sheets as real cheques, or the hand-picked examples as typical accuracy.
- Do not describe `accept` as fraud detection or authentication.
