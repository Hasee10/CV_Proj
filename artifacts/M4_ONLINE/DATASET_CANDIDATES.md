# M4-ONLINE: dataset candidates investigated (2026-11-26)

| # | Candidate | What was checked | Handwriting | Amount fields | Licence / access | Outcome |
|---|---|---|---|---|---|---|
| A | IDRBT Cheque Image Dataset (idrbt.ac.in) | page fetch with default and browser user agents | genuine (per user brief: 112 cheques, 9 volunteers) | yes | site **unreachable** (HTTP 000 / empty response, 3 attempts) | **blocked**: cannot verify or download |
| B1 | HF `arunchincheti/cheques_data` @ `cd99026…` | card, files, 130 test cheque rows, all images viewed | **synthetic** (handwriting-style fonts on 4 scanned bank templates; fixed date 06/05/22; Faker-style payees) | numeric + words annotated per cheque (`amt_in_figures`, `amt_in_words`) | Apache-2.0 declared; template provenance undocumented | **used as SYNTHETIC set D6** (amount-field crops only) |
| B2 | HF `arunchincheti/handwritten_and_cheques_dataset` | card, sample rows | same synthetic cheques + IAM text lines | same | IAM lines redistribute registration-gated data | not used |
| C | SSBI (dfki-av/bank-check-security, ICDAR'24) | README, repo licence | **synthetic** ("Synthetic Signature Bankcheck Images"; dummy text pasted into fields) | bounding boxes only (signature-focused) | repo licence "Other/NOASSERTION" | not used (synthetic, unclear licence, signature task) |
| D1 | ORAND-CAR (`elliot-mllm/OrandCar_*` on HF) | API metadata | genuine courtesy amounts from Chilean cheques | numeric only | **gated (manual approval)**, licence "other" | not used: access restriction |
| D2 | CVL Digit Strings, ICDAR 2013 HDSRC (Zenodo 1492173) | record, licence, train archive (MD5 verified), readme | **genuine** (about 120 writers) | numeric strings (10 distinct strings, incl. `25000`) | **CC-BY-NC-4.0**, open download | **used as GENUINE set D4** |
| D3 | GNHK test split (already cached, CC-BY-4.0) | all 10,066 word annotations | **genuine** | 36 English number words, 189 standalone integers 0–99 | CC-BY-4.0 | **used as GENUINE set D5** (constructed pairs) |
| D4 | HF `shivalikasingh/cheques_sample_data`, `aniketVerma07/*`, `07kamal03/*`, `kiranm2025/cheque`, `alpha-brain/ocr-synthetic-cheque-datatset` | cards and first rows | **synthetic** (same font-generator family or Faker US cheques) | yes | mostly no licence stated | not used (duplicate synthetic family, unclear licence) |
| D5 | HF `AnanOmri/handwritten-dates-numbers-ocr` | files | unknown | numbers and dates | **no licence** | not used |
| D6 | HF `TrevorJS/check-amount-verbalizer` | features | text only (no images) | n/a | none stated | not applicable |
| D7 | Zenodo AHLA (Arabic legal amounts), HF `SARAH-HADDAD/amount-in-*-words-dz` | search hits | Arabic / French | words | various | not English: out of scope |
| D8 | IAM | registration-gated; site unreachable in M4 | genuine | no amounts | non-commercial, registration | not used (access terms) |
| D9 | Google Dataset Search, Kaggle | not queried: Kaggle needs an account or API key; Dataset Search is a JS app | - | - | - | not searched (stated, not hidden) |

GitHub search for "handwritten legal amount english", "cheque legal amount dataset", "courtesy amount recognition dataset" and "handwritten number words dataset" returned no relevant repositories.

**Conclusion:** no openly downloadable dataset of *genuine English handwritten cheque amounts* (numeric plus words from the same cheque) was found. Genuine handwriting is available for numeric strings (CVL) and isolated English number words (GNHK). Cheque-level paired numeric and words fields are available only as synthetic font renders.
