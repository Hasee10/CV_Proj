# Third-party notices and attribution

| Component | Source | Version / revision | Licence | Use in this project |
|---|---|---|---|---|
| LoGoHTR code (Shree Mitra) | https://github.com/shreemitra/LoGoHTR | commit `9eaea5fe52e908ebf3b625ca4c05da3d1905a6af` | MIT (Copyright (c) 2026 Shree Mitra) | Unmodified in `third_party/LoGoHTR/`; imported by `scripts/smoke_inference.py` |
| CoMER (Wenqi Zhao, Liangcai Gao), on which LoGoHTR's `comer/` package is based | https://github.com/Green-Wood/CoMER | via LoGoHTR | See upstream CoMER repository (not re-verified in M3-A) | Indirect, through LoGoHTR |
| LoGo-HTR downstream checkpoint | https://huggingface.co/Shree10/LoGo-HTR `Downstream_Full_Model_Best.ckpt` | revision `64439ca9edfbf58e3007c2bb6af17559bcf2d29e`, SHA-256 `25db3a51…c432` | Apache-2.0 (model card tag) | Inference only, no training; not redistributed by default (`.gitignore`) |
| SSL-HWD Words (labelled) | https://huggingface.co/datasets/Shree10/SSL-HWD-Words | revision `91b51355f71e1166eb5b1ef3e6c0540463f32008` | Apache-2.0 (dataset card) | 8 word images taken from the first 4 MiB of the labelled zip for the smoke test |
| PyTorch, torchvision, PyTorch Lightning, torchmetrics, einops, OpenCV, NumPy, Pillow | PyPI / download.pytorch.org | see `requirements-inference.txt` | respective open-source licences | Runtime dependencies |

Paper: S. Mitra, A. Mondal, C. V. Jawahar. "Learning Beyond Labels: Self-Supervised Handwritten Text Recognition." WACV 2026, pp. 6653-6663.

## AI-assistance disclosure
The student reports that the instructor permits AI assistance, and that the guideline's ban on work by an "external party" refers to other students (recorded 2026-11-26). The M3-A environment setup, upstream/checkpoint acquisition, code inspection, the scripts `scripts/smoke_inference.py` and `scripts/fetch_ssl_hwd_samples.py`, and the M3-A documentation were produced with Claude Code (Anthropic) under the student's supervision. The student is responsible for reviewing, understanding and defending this work.
