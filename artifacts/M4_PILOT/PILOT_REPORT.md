# M4-PILOT report (2026-11-26, attempt 1): BLOCKED

## What was found
- `data/custom/raw/` is **empty**, and `data/custom/crops/` is empty. No `annotation.csv` exists.
- Search for a misnamed or misplaced photo:
  - The project tree, `Downloads`, `Desktop`, `Pictures` and `OneDrive/Pictures` (depth ≤ 5) were checked for files named `W01*` or `*sheet*`, and for JPG/PNG/HEIC images modified in the last 3 hours.
  - The only images found were the nine M3-B photos in `handwritten_examples/` (already known), plus template/data images excluded by path.
  - **No pilot photograph exists on disk.** One possibility is a OneDrive file that has not finished syncing to this PC.

## Pilot command (actual output)
```
> .\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract --only W01_A
ERROR: nothing to extract; problems: ['W01_A: no single valid photo found']
exit 1
```
Nothing was written (the script stops before writing any crop or annotation file).

## Acceptance criteria
| Criterion | Result |
|---|---|
| Genuine photograph processed | **not met**: no photograph |
| Four Sheet A markers (ids 0, 1, 2, 3) detected | not tested |
| Exactly 14 crops | 0 (not run) |
| Handwriting preserved, no prompt leakage, no box lines | not tested |
| Annotation entries and hashes | not created |
| Original photograph preserved | n/a |

`CONTACT_SHEET.png` was **not created**, because there are no crops. No placeholder image was made.

## Corrective action (student)
1. Make sure the photo file is actually on this PC. If it is in OneDrive, open the folder in File Explorer and confirm it shows as available (not "online-only" or still syncing).
2. Put it at `data/custom/raw/W01_A.jpg`. Any filename works; if it differs, Claude will make a correctly named byte-identical copy and keep the original.
3. Ask Claude to rerun M4-PILOT. Nothing needs to be redone on the code side.

## Pending corrections for custom finalisation (from the external review; not fixed now, since they do not block the pilot)
1. `read_annotations()` keys rows by `sample_id`, so **duplicate ids in the CSV can collapse silently** before `check_annotations` sees them.
2. `verified_value` goes through `Decimal()`, which **accepts `NaN`, `Infinity` and `sNaN`**. It should require a finite value, `>= 0`, with at most 2 decimals.
3. `numeric_value` uses `\d`, which in Python regex also matches **non-ASCII Unicode digits**, so mixed scripts (for example `١٢٣4`) may pass. It should use `[0-9]`. The current tests reject a pure Arabic-Indic string only because its first character fails `[1-9]`, not because of an explicit ASCII rule.

These must be fixed, with regression tests, before `custom_sheets.py finalize` is run on real data.
