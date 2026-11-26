# Custom dataset (D2): student collection instructions

## What you need
- **People:** at least **4 writers**, ideally **5–6**, including yourself as **W01**. Your handwriting is already in M3-B, so W01 always goes to dev. With only 4 writers the test set has 3 writers; with 5 it still has 3. **Minimum to proceed: 4 writers.**
- **Per writer:** the 3 sheets (A, B, C) in `data/custom/template/collection_sheets.pdf`, which gives 21 numeric + 21 written amounts. This takes about 15–20 minutes per writer.
- **Totals:** 4 writers give 84 pairs (168 crops); 6 writers give 126 pairs (252 crops). About 29% of pairs are deliberate mismatches (6 of 21).
- Volunteers should be adults who agree to take part. Tell them the sheets are fictional, used only for a course project, and identified only by a code. Keep no list linking codes to names in the project folder. Writers must not put their name, signature, account number or ID anywhere on a sheet.

## Steps
1. **Print** `collection_sheets.pdf` on A4 at **100% / actual size**, never "fit to page" (it rescales the markers and boxes). Print one A, B and C sheet per writer.
2. **Write.** Each writer copies every printed line exactly: the number into the short box, the words into the long box, in their normal handwriting with a dark blue or black pen. Mismatching pairs are intentional, so they copy exactly what is printed. They should not correct, cross out or redo anything. If a mistake happens, leave it; you record it during verification.
3. **Variety (optional):** ask one or two writers to write quickly, as on a real cheque. Don't coach anyone's style.
4. **Photograph** each sheet with a phone:
   - whole page in frame, with **all 4 black corner squares fully visible**;
   - flat on a table, roughly from above (a slight tilt is fine; the markers correct it);
   - normal indoor light, no flash glare and no hand shadow over the boxes;
   - default camera app, JPEG at full resolution, no filters or scanner apps.
   - Take one photo per sheet. If it's blurry or a marker is cut off, retake it and **replace** the file; never keep two photos of the same sheet.
5. **Name and place** the files in `data/custom/raw/` as **`W<nn>_<SHEET>.jpg`**, for example `W01_A.jpg`, `W01_B.jpg`, `W01_C.jpg`, `W02_A.jpg` and so on. Codes are W01 (you), then W02, W03… in the order people take part. Only you know who is who; keep that mapping outside the project, or nowhere.
6. **Extract crops:**
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract
   ```
   This writes `data/custom/crops/W<nn>_<ITEM>_<num|words>.png` and `data/custom/annotation.csv`, with each row prefilled with the printed prompt. If a photo is rejected ("markers not found"), retake it.
7. **Verify ground truth.** This is mandatory, and must be done before any model is run on these crops:
   - Open `data/custom/annotation.csv` in Excel and open each crop.
   - In `verified_text`, type **exactly what is written**, not what was printed. Usually the two are identical.
   - If they differ (a writer skipped a word or wrote a different digit), type what was written and put `yes` in `deviation`.
   - If a character is genuinely unclear, type your best reading and describe the doubt in `ambiguity_note`, for example `separator . or -`.
   - Put your initials in `verifier`. If possible, a second person checks the rows marked `deviation` or `ambiguity_note`.
   - Never look at model output during verification.
8. **Finalise** (builds the manifest, values, pair labels and the writer-disjoint split):
   ```powershell
   .\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py finalize
   .\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\custom\manifest.json --out artifacts\M4\VALIDATION_CUSTOM.json
   ```
   Both must succeed. Pair labels are recomputed from the verified values: if a writer accidentally made a matching pair mismatch, the label follows what was actually written.

Then tell Claude the photos and verification are done, so the M4 counts can be updated.

## File conventions
| Item | Pattern |
|---|---|
| Photo | `data/custom/raw/W<nn>_<A|B|C>.jpg` |
| Crop | `data/custom/crops/W<nn>_<ITEM>_<num|words>.png`, e.g. `W03_B04_words.png` |
| Sample id | same as the crop name without `.png` |
| Pair id | `W<nn>_<ITEM>` |
| Annotation | `data/custom/annotation.csv` (columns as in `data/custom/template/annotation_template.csv`) |

---
## Amendment M4-AUDIT (2026-11-26): what changed for you
- **Writing:** leave a **small margin inside each box** and do not touch the box lines (the crop trims about 8 px from each edge). Use natural handwriting. **Copy mismatching pairs exactly**: do not "fix" them.
- **Printing:** use actual size (100%) where practical. A uniform print scaling is not automatically fatal, because the markers correct global geometry, but it is untested. The W01_A pilot below decides.
- **Photos:** all four corner markers must be fully visible.
- **Pilot first (mandatory):** print and fill **sheet A only**, photograph it as `data/custom/raw/W01_A.jpg`, then run:
  ```powershell
  .\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract --only W01_A
  ```
  Open the 14 crops in `data/custom/crops/W01_A*.png`. Every crop must contain the whole handwriting and no box line or printed text. Only then collect the remaining sheets. Until a real photo has been checked this way, real-photo extraction is **not** verified.
- **Re-running is safe.** `extract` merges into `annotation.csv` and keeps a backup in `data/custom/annotation_backups/`. Verified rows are kept only if the photo and crop are byte-identical; a retaken photo resets its rows to `pending` with `reverify_reason` set. Use `--only W0x_Y` to process one photo. Extraction refuses to run once `manifest.json` exists.
- **Verification columns (replaces step 7):** for each row in `annotation.csv`:
  - **Faithful copy** (most rows): `verification_status=verified`, `deviation=no`, `verifier=<initials>`. Leave `verified_text`/`verified_value` blank; the designed value is used because you confirmed it. In Excel you can fill these three columns down.
  - **Writer deviated:** `verified`, `deviation=yes`, type the actual `verified_text` **and** its monetary `verified_value` (for example `12,000` / `12000`).
  - **Blank, illegible or ambiguous value:** `verification_status=unresolved` plus `unresolved_reason`. The row stays in the dataset without a value.
  - **Ambiguous punctuation only:** keep `verified`, and describe the doubt in `ambiguity_note`; that row is then excluded from strict punctuation scoring.
  - Never look at model output while verifying.
  - See `data/custom/template/annotation_template.csv` for one example of each case.
- `finalize` refuses until the set is complete (at least 4 writers including W01, sheets A-C each, all fields with a status, no re-verification pending), and lists exactly what is missing.
- Then validate:
  ```powershell
  .\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\custom\manifest.json --out artifacts\M4\VALIDATION_CUSTOM.json
  ```
  If it lists `near_duplicates_unresolved`, open each pair of images. Record your decision in `artifacts/M4/near_duplicate_review_custom.json` as `[{"pair": ["id_a", "id_b"], "decision": "not_duplicate", "reviewer": "XX", "note": ""}]` and re-run with `--resolved artifacts\M4\near_duplicate_review_custom.json` and a new `--out` name.
