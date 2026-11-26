# M4-ONLINE blockers and limitations

## Blocked or unavailable sources (not bypassed)
- **IDRBT Cheque Image Dataset:** site unreachable from this machine (3 attempts). It is the only known genuine English handwritten cheque set. If the student can open https://www.idrbt.ac.in/idrbt-cheque-image-dataset/ in a browser and its terms allow download, it can be added later as a further test set.
- **ORAND-CAR:** gated with manual approval on HF.
- **IAM:** registration-gated and unreachable. **Kaggle:** needs an account or API key (not used).

## Limitations of the acquired data (must appear in the report)
1. **No genuine handwritten cheque with both amount fields.** Cheque-level paired evaluation (D6) uses **synthetic font-rendered text**, so its results say nothing about handwriting recognition and must be reported separately from genuine sets.
2. **Genuine written amounts are minimal.** Only 27 GNHK single number words (values 1–11) exist; there are no multiword genuine written amounts. Multiword behaviour is covered by D6 (synthetic) and M3-B (exploratory) only.
3. **D4 CVL** has 10 distinct strings with no separators, decimals or currency. It tests unseen writers, not unseen amounts. Its licence is non-commercial (fine for coursework; restates the redistribution terms). Writer ids are inferred.
4. **Constructed pairs** (D5: 54, D6: 106) reuse crops and are not independent samples. They are not real fraud.
5. **D6 templates** are shared across dev and test, and its oracle boxes are template-specific. No automatic cheque-field detection exists.
6. **D5 dev** contains 1 word crop, so it cannot be used for tuning.
7. **Unknown checkpoint training data:** overlap with GNHK (a paper benchmark) cannot be ruled out. CVL and the synthetic cheques are unlikely training sources, but this is unverified.
8. Annotation checks are automated or AI visual checks. **No human verification was performed** on any online set.
9. Currency: the numeric grammar accepts only Rs / Rs. / PKR or none. D6 cheques use ₹ and S$ printed **outside** the crops; numeric crops contain digits only.

## Resolved in M4-ONLINE
The three pending review findings are fixed and tested:
- duplicate annotation ids now raise instead of collapsing;
- human values must be finite, non-negative and have at most 2 decimals;
- the numeric grammar is ASCII `[0-9]` only.

A latent crash on an empty `source_photo` was also fixed (`is_file()`).
