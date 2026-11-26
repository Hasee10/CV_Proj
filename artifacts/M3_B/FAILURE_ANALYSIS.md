# M3-B failure analysis: independent handwriting (exploratory, n = 9 samples)

The 9 samples were written and photographed by one student (a single writer, one pen, one phone camera, ruled paper). They are feasibility probes, not a benchmark, and the numbers below are not general accuracy. All predictions are raw outputs decoded with `SSL_HWD_Dict.txt`. Nothing was corrected.

## Per-sample observations (primary condition: neutral crop)

| ID | GT | Prediction | ED | Observed failure type |
|---|---|---|---|---|
| H01 | `2500` | `2500` | 0 | none |
| H02 | `12500` | `12500` | 0 | none |
| H03 | `50000` | `5000000` | 2 | extra characters: two extra `0` in a run of four identical glyphs |
| H04 | `1250.00` | `125000` | 1 | missing punctuation: decimal point dropped; all digits correct (GT decimal flagged ambiguous, drawn as a short dash) |
| H05 | `75,450.50` | `18050` | 6 | substitutions (`7`→`1`, `5`→`8`), missing characters (`4`, `5`), missing comma, missing decimal point |
| H06 | `Twenty` | `Twenty` | 0 | none |
| H07 | `Thousand` | `Inowand` | 4 | substitutions (`T`→`I`, `h`→`n`, `u`→`w`), missing `s`; the `Th` strokes are joined in the writing |
| H08 | `Rupees` | `Rupees` | 0 | none |
| H09 | `Five thousand only` | `Fivethousnandanty` | 5 | missing spaces (2), extra `n`, substitutions in `only`→`anty` |

Full-photo condition (unmodified photo): 1/9 exact. Its errors are extra `0`s (H02, H03), a `2`→`0` substitution (H01: `10500`), `.`→`0` (H04: `1250000`), digit reordering and extras with no punctuation (H05: `75405050`), case and substitution (H08: `ropees`) and a garbled line (H09: `Intiousantionly`). On the identical photos, the crop gave 4/9 and the full photo 1/9.

Segmented words of H09 (reported separately, not counted as line recognition): `Five`, `thousand` and `only` are all exact (3/3).

## Observed evidence (measured in this run)
1. **Punctuation was never emitted.** Ground truth contains 3 punctuation marks in each condition (H04 `.`, H05 `,` and `.`), and 0 were emitted in crop, full-photo or segmented runs. The vocabulary does contain `,` (id 15), `.` (17), `-` (16), `/` (18), `$` (7), `£` (93) and `₹` (96). Support in the vocabulary exists; recognition was not demonstrated.
2. **No space token.** Id 3 (the stripped space line, decoded as `""`) was emitted in 0 of 21 runs. The upstream decoder would render it as an empty string, so a space could not appear in the primary output even if emitted. The labelled `view_space_token_as_space` field equals the primary prediction in every row.
3. **Multiword line fails; the same words segmented succeed.** H09 line: 0/1 exact, CER 0.278 (5/18). Its three segmented words: 3/3 exact. Compared with the unspaced string `Fivethousandonly`, the line prediction still has edit distance 3.
4. **Plain digits are recognised.** H01 and H02 are exact, and in H04 all six digits are correct. Errors concentrate on repeated zeros (H03) and the longest formatted amount (H05).
5. **Cropping changes results, though not always for the better.** Exact matches: crop 4/9, full photo 1/9. By per-sample edit distance, the crop is better on 4 (H01, H02, H08, H09), tied on 3 (H04, H06, H07) and worse on 2 (H03: 2 against 1; H05: 6 against 3). Aggregate CER: crop 0.265, full photo 0.324. Full photos are downscaled to height 256 by `ScaleToLimitRange`, so the writing occupies a small part of the input.
6. **Latency scales with input size.** M3-A in-domain words (about 40–80 px tall) took 0.14 s median. Here crops are 145–256 px tall after upstream scaling, and the median is 1.11 s (crop) or 1.92 s (full photo). The H09 line took 6.1 s.

## Possible root causes (speculative; not tested in M3-B)
- **No space in the upstream training pipeline (code evidence, checkpoint not confirmed).** `comer/datamodule/datamodule.py:93-95` builds targets with `line.split()`, so a caption cannot contain a space token. If this checkpoint was trained through the same pipeline, the model never learned id 3 as a target. The checkpoint came from an earlier code revision (it monitors `val_ExpRate`), so this is likely but unconfirmed.
- **Word-level training data.** SSL-HWD is word-level (paper p. 6655), so multiword lines are out of distribution. This fits observation 3.
- **Punctuation rarity in training.** Amount formats like `75,450.50` are probably rare in SSL-HWD word crops. Table 2 counts 4,981 unique numeric words but gives no breakdown by format, so this cannot be checked from the paper.
- **Scale and domain shift.** Our crops are 2–5x taller than typical SSL-HWD word images, and `ScaleToLimitRange` keeps any height in 16–256. Other shifts: phone photos (illumination gradient, slight blur, grey paper) against scanned pages, and ruled lines crossing glyphs.
- **Repetition errors** on runs of identical glyphs (`0000`) are a known behaviour of attention decoders. This is a hypothesis only.

## What is not a cause (checked)
- Unreadable inputs: none (all 21 passed the PIL verify step).
- Cropping problems: the contact-sheet check shows every crop contains the complete ink. The H09a cut between `e` and `t` is noted in the manifest, and H09a still decoded correctly.
- Vocabulary mismatch: the `SSL_HWD_Dict.txt` choice is reconfirmed. `dictionary.txt` again yields shifted text (`Twenty`→`Tvdmsx`).

No improvement was implemented. Candidate directions for a later milestone, all unverified hypotheses: neutral height normalisation before inference, word segmentation for written amounts, and amount-format handling for punctuation.
