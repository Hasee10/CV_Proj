# M4-FINAL integrity report (2026-11-26)

Evidence is in `INTEGRITY_EVIDENCE.json` (`scripts/audit_integrity.py`) and `VALIDATION_REPORT.json`. All checks are automated or AI visual checks; **no human review is claimed**.

## IDRBT direct download
- Attempted `https://www.idrbt.ac.in/wp-content/uploads/2022/07/IDRBT_Cheque_Image_Dataset.zip` twice (90 s timeout), plus the bare-domain URL once. All failed with `curl: (6) Could not resolve host`.
- The local resolver returned "Server failed"; a lookup via 8.8.8.8 returned the name but no address.
- **Not acquired**, and no further attempts were made. The genuine multiword written-amount gap remains.

## Duplicate audit (beyond label differences)
- All 227 earlier candidates were re-scored on pixels (ink-mask IoU and mean absolute grey difference at 256×64) and lineage. The duplicate rule: same source image, or IoU ≥ 0.85 **and** grey difference ≤ 8 **and** the same non-blank text.
- **Result:** 213 distinct and 14 blank template regions; **0 true duplicates**.
  - Highest IoU among distinct pairs: 0.918 (`SYN_0121_words` "…Seventy Four" vs `SYN_0275_words` "…Seventy Six": same font and template, different words, AI-checked).
  - 95th-percentile IoU: 0.652.
- **Lineage:** 130 distinct synthetic source images, none in two splits. Repeated texts (`1550` and `4376`, both numeric and words) occur only within test, with IoU ≤ 0.19 (different fonts).
- **Byte-identical images:** 872 entries hold 854 unique hashes. All 8 shared-hash groups are blank synthetic numeric fields, and 3 of them span dev and test. They carry no handwriting.
  - **Rule:** blank fields are not eligible for recognition metrics and are reported separately (dev 6, test 18).
- **Synthetic correlation:** dev and test share the same 4 templates and a limited set of fonts, so D6 samples are correlated. D6 is reported per template, and never pooled with genuine sets. A template-disjoint view is left as a supplementary analysis; the primary split is unchanged, since no integrity problem was found.

## Provenance
- **CVL:** the archive readme describes the second filename field only as "an unique ID". It is **not documented as a writer id**, so we use it as an *inferred* writer/session id; 121 of 127 ids hold exactly one copy of each of the 10 strings. Writer-disjointness is therefore inferred, not confirmed. CC-BY-NC-4.0.
- **GNHK D1/D5:** 312 entries, 309 unique hashes, 3 shared crops, 127 unique pages (30 shared), 0 page-split conflicts.
- **Synthetic cheques:** Apache-2.0 is declared on the Hugging Face card only. The underlying templates are real bank layouts with undocumented provenance. We keep the set for research evaluation because:
  - the crops contain only the two amount fields (font-rendered text, small printed fragments);
  - no logo, account number, MICR line, payee or signature is included;
  - full cheque images stay in the git-ignored cache.
  - Their permission is a declared-licence assumption, recorded as a limitation. D6 is **not genuine handwriting and not genuine bank-cheque evaluation**.

## Eligibility rules (frozen)
- **Recognition:** `ground_truth` non-empty. Excluded: 24 blank synthetic fields.
- **Amount value:** `gt_value` present (D4, D5, D6). D1 has no amount values.
- **Pairs:** `label` is `match` or `mismatch`. The 24 `unresolved` pairs (blank field) are reported separately and count toward review behaviour only.

## Status
**M4: VERIFIED WITH DOCUMENTED LIMITATIONS.** The manifests are unchanged from M4-ONLINE and are frozen with the hashes in `SUMMARY.json`.

## Limitations
- CVL has 10 fixed strings and a non-commercial licence.
- GNHK number words are isolated words, and D5 dev is tiny (3 crops, 2 pairs).
- Constructed pairs reuse crops.
- Synthetic templates and fonts repeat across splits.
- The checkpoint's training data is unknown.
- No arbitrary cheque-field detection exists.
- Annotation checks were AI-assisted, not human.
