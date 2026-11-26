# M5-DEV preliminary failure inventory (descriptive only)

These are automatic categories from `scripts/score_baseline.py` (alignment-based, multi-label) over the **171 wrong predictions among 245 eligible dev samples**. One sample can fall into several categories. No improvement was implemented or tested.

| Category | Samples | By set | Example (id: ground truth → prediction) | Financial consequence |
|---|---|---|---|---|
| Invalid financial parse (value-bearing field, parser returns None) | 76 | D6 68, D4 7, D5 1 | CVL_136075_0021_03: `136075` → `13607T` | routed to review |
| Letter substitution | 62 | D1 25, D6 37 | GNHK_eng_AF_010_w003: `you` → `fou` | - |
| Digit substitution | 48 | D4 42, D6 4, D1 2 | CVL_135579_0002_10: `135579` → `135529` | wrong value whenever the prediction still parses |
| Letter omission | 44 | D6 37, D1 7 | GNHK_eng_EU_174_w018: `improve` → `mprove` | - |
| Multiword line collapsed, no space emitted | 37 | D6 37 | SYN_0013_words: `One Thousand Seven Hundred and Thirty Seven` → `comansinsuratimen` | written amount unparseable → review |
| Letter insertion | 15 | D1 10, D6 4, D4 1 | GNHK_eng_AF_061_w003: `onions.` → `Donemons` | - |
| Digit insertion / omission (other) | 10 | D4 5, D1 5 | CVL_359910_0230_07: `359910` → `3592910`; CVL_5841077_0021_04: `5841077` → `584077` | value off by about ×10 |
| Other punctuation (`:`, `-`, `/`, brackets) | 7 | D1 7 | GNHK_eng_NA_047_w098: `3:` → `3.` | - |
| Case error | 6 | D1 4, D6 2 | GNHK_eng_EU_210_w011: `press` → `Prey` | - |
| Missing or wrong decimal point | 5 | D1 5 | GNHK_eng_AS_007_w062: `4.` → `A` | - |
| Missing or wrong thousands separator | 3 | D1 3 | GNHK_eng_NA_142_w051: `(225,000)` → `(225.000)`; GNHK_eng_NA_047_w088: `25,000,000` → `2500000000` | comma read as a decimal point gives a ×1000 value error |
| Repeated-zero deletion | 1 | D1 1 | GNHK_eng_NA_142_w079: `377,480-368,480` → `379808588898` | - |

Also observed:
- **CVL** `25000`: one prediction `260000` (an extra digit; zero run kept), one `75000` (a digit substitution). The other 7 of 9 were exact.
- **Zero runs:** only 1 repeated-zero deletion and 0 insertions were detected on dev. The M3-B repeated-zero errors (photographed crops) do not reappear in scanned CVL.
- **Currency notation:** none present in the dev crops, so not evaluated.
- **Pair outcomes:** 0 false acceptances and 0 false rejections, because 73 of 74 dev pairs went to review (all 72 synthetic, plus 1 GNHK).
- **Slow inference (> P95 = 1.70 s), 12 cases:**
  - 9 synthetic words lines (2.1–4.6 s);
  - 3 large GNHK crops (2.3–8.3 s; widths of 839–1024 after scaling).
- **Image quality and crops (from the M4 audits):**
  - D6 crops are low-resolution, about 30 px text lines, and contain printed lines and label fragments;
  - several GNHK integer crops are only a few pixels tall;
  - one D5 integer `7` was read as `a`.

Candidate root causes, to test in M6 and not established here: input scale (small synthetic text), multiword lines without spaces, font-rendered rather than handwritten domain, and punctuation rarity.
