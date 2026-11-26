# M3-B failure analysis (corrected ground truth, revision 2)

This file supersedes `artifacts/M3_B/FAILURE_ANALYSIS.md` for ground truth and derived metrics only. The model outputs are the original M3-B predictions, unchanged. The samples are exploratory: 9 samples from one writer, not a benchmark.

## Ground-truth review after visual audit
| ID | Original M3-B GT | Final GT | Handling |
|---|---|---|---|
| H04 | `1250.00` | `1250-00` (alternative `1250.00` scored) | Separator ambiguous (a short, slightly sloped stroke at mid-low height, closer to `-` than `.`). **Excluded from strict punctuation evaluation**; both readings scored |
| H05 | `75,450.50` | `75,450.50` (unchanged) | The audit proposed `75,430.50`. Revision 1 adopted it as disputed. Revision 2 reverted it after **the writer confirmed `75,450.50`**, which agrees with a side-by-side comparison against the writer's other `5` glyphs |

Unchanged (confirmed): `2500`, `12500`, `50000`, `Twenty`, `Thousand`, `Rupees` and `Five thousand only` (very narrow gap after `Five`).

**H04 decision.** I keep the sample and score both readings, but exclude its separator from strict punctuation scoring. Dropping H04 would discard six clearly written digits. Forcing one reading would hide a real uncertainty. The model emitted no separator (`125000`), so ED = 1 under either reading, and H04's choice cannot change any aggregate.

## Per-sample results (crop condition, original predictions)
| ID | GT | Prediction | ED | CER | Observed failure type |
|---|---|---|---|---|---|
| H01 | `2500` | `2500` | 0 | 0 | none |
| H02 | `12500` | `12500` | 0 | 0 | none |
| H03 | `50000` | `5000000` | 2 | 0.400 | extra repeated `0` (2) |
| H04 | `1250-00` (alt `1250.00`) | `125000` | 1 (alt 1) | 0.143 | separator missing; all 6 digits correct |
| H05 | `75,450.50` | `18050` | 6 | 0.667 | digit substitutions, missing digits, missing comma, missing decimal point |
| H06 | `Twenty` | `Twenty` | 0 | 0 | none |
| H07 | `Thousand` | `Inowand` | 4 | 0.500 | substitutions on joined `Th`, `u`→`w`, missing `s` |
| H08 | `Rupees` | `Rupees` | 0 | 0 | none |
| H09 | `Five thousand only` | `Fivethousnandanty` | 5 | 0.278 | missing spaces (2), extra `n`, `only`→`anty` |

Full photos and segmented words: per-sample results are identical to the original M3-B.

## Sensitivity to the H04 reading
| H04 reading | Crop exact / CER | Full-photo exact / CER |
|---|---|---|
| `1250-00` (primary) | 4/9, 0.2647 | 1/9, 0.3235 |
| `1250.00` | 4/9, 0.2647 | 1/9, 0.3235 |

## Observed evidence
1. **Punctuation, strict:** 0 of 2 unambiguous marks emitted (H05's comma and decimal point, in both crop and full photo). H04's separator is excluded as ambiguous, and the model emitted nothing there either. Punctuation recognition remains undemonstrated.
2. **No space token** in any of the 21 runs.
3. **Multiword line 0/1; segmented words 3/3.**
4. **Plain digits are recognised:** H01 and H02 are exact, and H04's six digits are correct. Crop numeric is 2/5 exact, CER 0.300.
5. **Crop compared with full photo:** exact 4/9 against 1/9, aggregate CER 0.2647 against 0.3235.
6. **Latency:** median 1.11 s per crop.

Speculative causes are unchanged from M3-B: word-level training without space targets (`datamodule.py:93-95` uses `str.split()`), rarity of formatted amounts, scale mismatch, photo-versus-scan shift, and repetition on identical glyphs. None was tested. No improvement was implemented.

## Net change from original M3-B
Only H04: the primary GT is `1250-00` with `1250.00` as an alternative, and the sample is excluded from strict punctuation, which changes the punctuation denominator from 3 to 2. Every exact-match, CER and latency figure equals the original M3-B.
