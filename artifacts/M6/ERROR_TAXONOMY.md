# M6 error taxonomy (clean dev, 171 wrong of 245 eligible; multi-label)

The categories come from `scripts/score_baseline.py::classify`, which aligns prediction and ground truth with a deterministic Levenshtein alignment.

| Category | Definition | Count | By group | Financial relevance |
|---|---|---|---|---|
| invalid_financial_parse | value-bearing field whose prediction the frozen grammar cannot parse | 76 | D6 words 37, D6 numeric 31, D4 7, D5 1 | routes the pair to review |
| letter_substitution | a letter replaced by a different letter | 62 | D6 words 37, D1 25 | wrong written amount |
| digit_substitution | a digit replaced by a different digit | 48 | D4 42, D6 numeric 4, D1 2 | wrong value if it still parses |
| letter_omission | a GT letter missing | 44 | D6 words 37, D1 7 | - |
| missing_space / multiword_collapsed | GT space not produced; multiword line output without spaces | 37 / 37 | D6 words 37 | written amount unparseable |
| letter_insertion | an extra letter | 15 | D1 10, D6 numeric 4, D4 1 | - |
| other | errors not covered above, mainly digit insertions and omissions | 10 | D1 5, D4 5 | value off by about ×10 |
| other_punctuation_error | `: - / ( )` wrong or missing | 7 | D1 7 | - |
| case_error | same letter, wrong case | 6 | D1 4, D6 words 2 | - |
| missing_or_wrong_decimal_point | GT `.` missing or substituted | 5 | D1 5 | can change the value ×100 |
| missing_or_wrong_thousands_separator | GT `,` missing or substituted | 3 | D1 3 | ×1000 if read as `.` |
| repeated_zero_deletion | a `0` deleted from a run of zeros | 1 | D1 1 | ×10 |

Stress adds no new categories. It mainly raises digit substitutions (213–235 per corruption family) and gives 1–7 zero insertions per family (`DIAGNOSTIC_RESULTS.json` DX-E).
