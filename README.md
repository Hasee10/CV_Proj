# ChequeVerify

Handwritten cheque amount recognition and discrepancy checking, built on a published handwriting recogniser and evaluated with reproducible, hash-checked data.

ChequeVerify reads the two amount fields on a cheque: the number (for example `12,500`) and the amount in words (for example "Twelve thousand five hundred only"). It converts both to values and flags a cheque for review when they disagree. The recogniser is LoGo-HTR (Mitra, Mondal and Jawahar, *Learning Beyond Labels: Self-Supervised Handwritten Text Recognition*, WACV 2026), used with the authors' released checkpoint on CPU and without retraining.

This is an academic prototype for the Computer Vision course (FAST-NUCES, Fall 2026). It is not bank clearing software, and every flagged cheque is meant for a person to review.

## Status

| Milestone | State | Evidence |
|---|---|---|
| M3-A: checkpoint and CPU inference | verified | strict load of all 673 weight tensors (6,385,537 parameters); 8/8 preselected words read exactly; median 0.14 s per word |
| M3-B: independent handwriting check | verified (exploratory) | 9 photographed samples from one writer: 4/9 exact on crops, CER 0.2647; punctuation and spaces never emitted |
| M4: datasets and evaluation design | verified, with documented limits | 872 validated samples across four sets; 38/38 regression tests pass |
| M5-DEV: frozen baseline on the dev split | verified | 251 dev entries, 0 errors; exact matches: GNHK words 34/80, CVL digit strings 38/90, synthetic cheque fields 0/72; every synthetic amount pair goes to review |
| M5 test, M6 onward: locked test, failure analysis, improvement, web demo | not started | |

Each milestone has its evidence in `artifacts/<milestone>/` (summary JSON, commands, logs, hashes). `PROJECT_TRACKER.md` holds the running log, and `ROADMAP.md` describes every phase, its deliverables and the rules for contributors.

## What the early experiments found

On nine photographed samples (2,500 to 75,450.50, plus words such as "Twenty" and "Five thousand only"), the model read plain digits and single words well but never produced a comma, a decimal point or a space. Recognition on the full photographs was worse than on neutral crops: 1/9 exact against 4/9. The three words of "Five thousand only" were each read correctly when cropped one at a time, but the full line came out as `Fivethousnandanty`. These nine samples come from one writer, so they show behaviour rather than accuracy. They set the questions for the formal evaluation in M5 and M6.

## Evaluation data

| Set | Handwriting | Size (dev / test) | Licence |
|---|---|---|---|
| GNHK test-split word subset | genuine, phone photos | 240 words (80 / 160), split by page | CC-BY-4.0 |
| CVL digit strings (ICDAR 2013) | genuine, about 120 writers | 300 strings (90 / 210), split by writer | CC-BY-NC-4.0 |
| GNHK number words vs integers | genuine | 72 crops, 54 constructed pairs (27 match, 27 mismatch) | CC-BY-4.0 |
| Synthetic cheques (`arunchincheti/cheques_data`) | **synthetic**: font-rendered | 260 amount crops from 130 cheques, 236 pairs | Apache-2.0 (declared) |

No openly downloadable dataset of genuine English handwritten cheques was available: the IDRBT site was unreachable and ORAND-CAR is gated. The cheque-level pairs are therefore synthetic, and their results are always reported apart from the genuine sets. Ground-truth values come from the dataset labels through rules that do not touch the recogniser or the parsers under test. All splits use seed `20261126`, and a validator rejects any group, writer or amount pair that crosses dev and test. Full details are in `artifacts/M4_ONLINE/DATASET_CARD.md`.

## Repository layout

```
scripts/            inference adapter, dataset builders, metrics, validators, stress corruptions
tests/              regression suites (tests/test_m4_audit.py, tests/test_m4_online.py)
data/benchmarks/    CVL, GNHK-pair and synthetic-cheque crops with manifests and amount_pairs.json
data/public/gnhk/   GNHK word subset and manifest
data/handwritten_examples/  M3-B photographs, crops and frozen manifest
artifacts/          per-milestone evidence (M3_A ... M4_ONLINE)
```

The model checkpoint, the upstream LoGo-HTR code and the raw dataset archives are not stored here. The commands below fetch them and check their hashes.

## Setup (Windows, CPU)

Python 3.11 is required.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
git clone https://github.com/shreemitra/LoGoHTR third_party/LoGoHTR
git -C third_party/LoGoHTR checkout 9eaea5fe52e908ebf3b625ca4c05da3d1905a6af
New-Item -ItemType Directory -Force models/logo_htr
curl.exe -L -o models/logo_htr/Downstream_Full_Model_Best.ckpt "https://huggingface.co/Shree10/LoGo-HTR/resolve/64439ca9edfbf58e3007c2bb6af17559bcf2d29e/Downstream_Full_Model_Best.ckpt"
```

The expected SHA-256 of the checkpoint is `25db3a51f70a08cd5cbbf88409470bc4b37821aff95bc5ee6ab89e1e4298c432`, and the inference script refuses to load anything else.

## Usage

Recognise one image (the output path must be new; existing evidence is never overwritten):

```powershell
.\.venv\Scripts\python.exe -X utf8 -I scripts\smoke_inference.py path\to\word.png --out results\my_run.json
```

Rebuild and validate the evaluation data:

```powershell
.\.venv\Scripts\python.exe -I scripts\fetch_gnhk_test.py
.\.venv\Scripts\python.exe -X utf8 -I scripts\fetch_online_data.py cvl
.\.venv\Scripts\python.exe -X utf8 -I scripts\fetch_online_data.py hf
.\.venv\Scripts\python.exe -X utf8 -I scripts\build_online_benchmarks.py
```

Run the tests:

```powershell
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m4_online.py
```

The exact commands behind every recorded result are in each milestone's `COMMANDS.md`.

## Design choices worth knowing

- The upstream code was written for PyTorch Lightning 1.4. It runs unmodified on current CPU builds through two small adapters in `scripts/smoke_inference.py`. One points the vocabulary at `SSL_HWD_Dict.txt`, because upstream names a file that is missing from its repository. The other skips a hard-coded Linux path for the encoder pre-load. A strict full-checkpoint load then replaces every weight.
- The vocabulary was chosen by experiment. Two shipped dictionaries both give the checkpoint's 97 tokens; only `SSL_HWD_Dict.txt` decodes lowercase letters correctly, while the other shifts each letter by one (`living` becomes `khuhmf`).
- Amount parsing in `scripts/eval_metrics.py` is strict. It accepts `2,500`, `1,50,000`, `Rs. 3,000/-` and "One lakh fifty thousand only", and sends malformed input such as `12,50`, `1,,250` or "five five" to manual review. It never repairs a missing decimal point.
- A failed inference counts as an empty prediction, so failed samples cannot drop out of the scores.

## Limitations

- The checkpoint's fine-tuning data is not documented, so overlap with GNHK cannot be ruled out.
- Genuine handwritten written amounts in the evaluation data are limited to 27 single number words.
- Every crop comes from a known position (annotation boxes or fixed template boxes). Automatic cheque-field detection is not implemented.
- Signature verification and tampering detection are out of scope.

## Credits and licences

- LoGo-HTR code: Shree Mitra, MIT licence (cloned at commit `9eaea5f`, not modified). Checkpoint: Apache-2.0, Hugging Face `Shree10/LoGo-HTR`.
- GNHK: Lee, Chung and Lee, ICDAR 2021, CC-BY-4.0. CVL Digit Strings: Diem et al., ICDAR 2013, CC-BY-NC-4.0 (non-commercial use). SSL-HWD samples: Apache-2.0.
- Full attribution, including the AI-assistance disclosure required by the course rules, is in `THIRD_PARTY_NOTICES.md`.
