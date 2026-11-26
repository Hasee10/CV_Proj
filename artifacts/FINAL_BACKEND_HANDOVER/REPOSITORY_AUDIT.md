# Repository audit before the push (27 Nov 2026)

- **Remote:** `origin` = https://github.com/Hasee10/CV_Proj.git, branch `main`. The remote `main` was at `570ffe1` (M6) before this push.
- **Commits pushed:** f836129 (M7), 5520d75 (M8), 56b9df1 (M9-A), 1ad9199 (M10-A), 1448d7a (backend timeout fix and demo inputs), 9ca5789 (line endings), and the final handover commit.
- **Author on all of them:** `ALICANFLY0 <ALICANFLY0@users.noreply.github.com>`. History was not rewritten and nothing was force-pushed.

## Checks
| check | method | result |
|---|---|---|
| API keys, tokens, private keys | `git grep` over every revision in the repository for Hugging Face, GitHub, OpenAI-style, AWS and Slack token shapes, PEM private keys, and `password/secret/api_key/access_token = "..."` (scanner sanity check: a known string returned 55 hits) | 0 hits |
| model weights, venvs, credentials, `.env` | every path ever committed, matched against `.ckpt .pth .pt .venv/ node_modules .env credentials models/ third_party/ research/` | none |
| `data/custom/raw/11.jpeg` (personal photo) | path history and working tree | never committed; still untracked and excluded |
| large binaries | blobs over 1 MB added in the pushed range | none (largest additions are result JSON files under 1 MB) |
| e-mail addresses | `@gmail.com` pattern in tracked files | none |
| local machine identifiers | Windows user name in tracked files | 2 historical files, see finding 1 |
| images added in this push | listed and checked | 4 result charts (`artifacts/M8/figures/`, generated from saved metrics) and 3 demo composites (`data/demo/`) built from licensed dev crops; no cheque, signature or personal data |
| restricted datasets | licence of every tracked dataset image | see below |

## Dataset redistribution
All tracked dataset images were already in the remote before this push (added in M3–M4). The demo composites reuse three of them.

| data | licence recorded | note |
|---|---|---|
| GNHK word and number crops | CC-BY-4.0 | attribution in README |
| CVL digit strings | CC-BY-NC-4.0 | non-commercial use; fine for coursework, but any commercial reuse of the repository would need these files removed |
| synthetic cheque crops (HF `arunchincheti/cheques_data`) | Apache-2.0 (declared on the dataset card) | the provenance of the underlying bank templates is undocumented; only cropped amount fields are stored, not full cheques |
| SSL-HWD smoke samples | Apache-2.0 | 8 words |
| `handwritten_examples/` and `data/handwritten_examples/` | the student's own handwriting | committed by the student in 7e9682d and already public |

A private repository would not change these licence terms. The non-commercial CVL licence still applies.

## Findings
1. **Windows user name in two historical evidence files.** `artifacts/M3_A/ENVIRONMENT.json` and `artifacts/M3_A/run1_stdout.log` record the original project path, which includes the local Windows user name. They have been public since an earlier push. This is a machine identifier, not a credential, so the push went ahead. Removing it from history would need a history rewrite, which is out of scope. The files can be redacted in a normal future commit if the student wants.
2. **Line endings** (fixed before the push in 9ca5789; see [REPRODUCTION_REPORT.md](REPRODUCTION_REPORT.md)).
3. **Public visibility.** The repository is public, and visibility was not changed. Everything listed above is suitable for a public coursework repository under the recorded licences.
