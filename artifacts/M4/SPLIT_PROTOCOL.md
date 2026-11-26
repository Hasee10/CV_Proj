# M4 split protocol and leakage prevention

Seed for every split: **20261126** (Python `random.Random(seed).shuffle` on a sorted list).

## D1 GNHK subset (applied)
- **Unit:** the page, used as a proxy for writer (GNHK has no writer ids, so writer-disjointness is **not verifiable**).
- **Algorithm:** sort the 172 test page ids, shuffle with the seed, assign the first `round(0.3 × 172) = 52` pages to dev and the remaining 120 to test. Words are then sampled within each split (`build_gnhk_subset.py`).
- **Actual counts:** dev 80 words from 42 pages; test 160 words from 80 pages.
- **Validation** (`scripts/validate_manifest.py`, report `VALIDATION_GNHK.json`): 240/240 files present, all SHA-256 values match, all readable. No group (page) spans splits. 0 cross-split exact duplicates and 0 near-duplicate candidates (64-bit dHash, Hamming ≤ 4). **Passed.**

## D2 Custom amounts (procedure fixed; applied after collection)
- **Unit:** the writer (writer-disjoint). All crops from one photo (`group_id`), and both fields of a pair, follow their writer.
- **Algorithm** (`custom_sheets.py finalize`): `n_dev = max(1, round(0.3 × n_writers))`. `W01` (the M3-B writer, whose handwriting has already been seen) is forced into dev. The other writers are sorted, shuffled with the seed, and used to fill the remaining dev slots. Everyone else goes to test.
  - Example: 5 writers gives 2 dev (W01 plus one) and 3 test.
- **Repeat photos** of the same sheet keep the same writer and so the same split. A retake replaces the original file; it is never added as a second sample.
- **Validation:** `validate_manifest.py data/custom/manifest.json` must pass (hashes, writer and group consistency, exact and near duplicates) before any evaluation.

## D3 Stress variants
Every variant has `parent_id` and inherits the parent's split. The validator rejects any variant whose split differs from its parent.

## D0 M3-B
Exploratory and development-only. It is never test evidence. Its observations (repeated zeros, missing punctuation, no spaces) motivated the hypotheses, so they cannot also confirm them.

## Rules for later milestones
1. Test labels, split assignments and manifest hashes are frozen before comparative evaluation. Record the manifest SHA-256 in the milestone summary.
2. Enhancement methods and their parameters are chosen on **dev only**. Test is run once per frozen system.
3. Baseline and improved systems are evaluated on identical sample ids.
4. Ambiguous labels keep both readings, and their ambiguous characters are excluded from strict punctuation scoring (the M3-B H04 precedent).

---
## Amendment M4-AUDIT (2026-11-26)
- **Custom writers.** Five writers is the preferred target: the rule gives 2 dev (W01 plus 1) and 3 test. Four is the minimum: 1 dev (W01) and 3 test. `finalize` enforces at least 4 writers, W01 present and in dev only, sheets A-C for every writer, all 21 pairs x 2 fields, unique ids, unique writer/item/field, a status on every row, and valid source and crop hashes. Otherwise it reports PARTIAL with the exact missing items.
- **Same-amount limitation.** Every writer copies the same 21 pairs, so a writer-disjoint split tests **unseen handwriting styles, not unseen amount expressions**. Results must not be read as generalisation to new amount wordings.
- **Inputs to recognition.** Only the cropped handwriting image is given to the baseline or the improved recogniser. Printed prompts, the amount list, design labels and verified ground truth are never inputs. They live in the manifest for scoring and analysis only.
- **Near duplicates.** Candidates are reviewed by a person (`--resolved`), never deleted automatically. Similar-looking amounts written by different people are legitimate. Blank or near-blank fields are a known source of false-positive candidates (shown by the synthetic blank-sheet regression fixture).
