# M4-ONLINE: selection and justification

The custom collection workflow is retired by the student's decision. Each source was chosen on availability, provenance and handwriting authenticity, never on recognition performance (no inference was run).

| Set | Role | Why selected | Main limitation |
|---|---|---|---|
| **D1 GNHK subset** (M4, unchanged) | standard public benchmark, word level | paper benchmark, CC-BY-4.0, phone-photo handwriting | page-disjoint only; digit-enriched |
| **D4 CVL numeric** (genuine) | handwritten numeric amounts | the only open, licence-clear, genuine multi-writer digit-string set; inferred writer ids allow a writer-disjoint split; includes repeated zeros (`25000`) | 10 distinct strings, no separators, decimals or currency; scanned forms, not cheques; CC-BY-NC (non-commercial use only) |
| **D5 GNHK number pairs** (genuine) | genuine numeric vs written-word agreement | genuine English number words exist only in GNHK among accessible data | 27 word crops, values 1–11, single words (not multiword amounts); pairs constructed across pages and writers; dev has 1 word |
| **D6 synthetic cheques** | cheque-level numeric + words fields, natural and constructed mismatches, blank fields | only accessible source with both amount fields annotated per cheque; real cheque layouts; includes 14 natural discrepancies and 24 blank fields | **synthetic font-rendered text**, not handwriting; 4 templates shared by dev and test; template-specific oracle boxes; real bank branding on templates (excluded from crops) |

## Sizes acquired
- **D4:** CVL train archive, 15.8 MB (1,262 images, 127 inferred writers). Selected 30 writers × 10 strings = **300 crops** (dev 90 / test 210).
- **D5:** from the cached GNHK test archive (no new download): **72 crops**, 27 number words and 45 integers (dev 3 / test 69), giving **54 pairs** (27 match / 27 mismatch).
- **D6:** 130 synthetic cheques, 2.7 MB via the HF rows API (182 IAM-line rows skipped). **260 crops** (130 numeric + 130 words; dev 78 / test 182) in **236 pairs**:
  - 92 natural match;
  - 14 natural mismatch;
  - 24 unresolved (blank field);
  - 106 constructed mismatch.

## Not claimed
None of this is real bank cheque data with genuine handwriting in both fields. D6 is not handwriting. Constructed mismatches are not fraud. Genuine and synthetic results must be reported separately.
