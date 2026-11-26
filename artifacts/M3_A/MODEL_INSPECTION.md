# M3-A model inspection: LoGo-HTR downstream checkpoint

Upstream: https://github.com/shreemitra/LoGoHTR, commit `9eaea5fe52e908ebf3b625ca4c05da3d1905a6af` (2026-05-22, "Added Pretraining Code"), working tree clean, MIT licence. Paths below are relative to `third_party/LoGoHTR/`. Paper pages refer to the WACV 2026 printed page numbers in `research/paper2/paper2.pdf`.

## 1. Architecture (code, checkpoint and paper agree)

| Item | Code (source) | Checkpoint `hyper_parameters` | Paper |
|---|---|---|---|
| Encoder | DenseNet-B, 3 dense blocks, bottleneck, reduction 0.5, dropout 0.2 (`comer/model/encoder.py:14-139`) | growth_rate 24, num_layers 16 | 3 blocks x 16 bottleneck layers, k=24, p=0.2, θ=0.5 (p. 6658) |
| Stem | conv 7x7 stride 2, 3 input channels -> 48, max-pool 2 (`encoder.py:86-89,125-129`) | `conv1.weight` (48,3,7,7) | - |
| Encoder output | 684 channels -> 1x1 conv to d_model, 2-D sinusoidal position encoding, LayerNorm (`encoder.py:162-174`) | `feature_proj.weight` (256,684,1,1) | 2-D positional encoding (Fig. 2, p. 6656) |
| Decoder | CoMER Transformer decoder with ARM coverage (`comer/model/decoder.py:18-76`) | d_model 256, nhead 8, 3 layers, FFN 1024, dropout 0.3, dc 32, cross+self coverage | 3 layers, 256, FFN 1024, dropout 0.3, 8 heads, coverage (p. 6658) |
| Output | Linear 256 -> vocab_size (`decoder.py:76`) | `proj.weight` (97,256) | - |

Parameter count of the loaded model: **6,385,537** (encoder 3,161,328; decoder 3,224,209), plus 142,133 BatchNorm buffer values. The paper reports 6.4M (Table 3, p. 6659). The difference is rounding only.

## 2. Vocabulary and special tokens

- `comer/datamodule/vocab.py:13-26`: PAD=0, SOS=1, EOS=2. Then one token per dictionary line, `line.strip()`, so the leading space line becomes the empty-string token (index 3).
- `vocab.py:7-8` defaults to `IIIT_Dict.txt`. **That file is not in the repository.** Upstream `import comer.datamodule` therefore fails with `FileNotFoundError`.
- Shipped dictionaries: `IAM_Dict.txt` (79 lines -> 82 tokens), `RIMES_Dictionary.txt` (98 -> 101), `dictionary.txt` (94 -> 97) and `SSL_HWD_Dict.txt` (94 -> 97).
- The checkpoint has 97 output tokens. That rules out IAM and RIMES but cannot separate `dictionary.txt` from `SSL_HWD_Dict.txt`. Both files are identical up to `^`. Then `dictionary.txt` inserts `_`, so every lowercase letter sits one index later than in `SSL_HWD_Dict.txt`. The tail also differs: `{ | } ~ £` against `{ } £ ¥ ° ₹`.
- **Resolution (empirical, stated before inference):** the model emits token ids, and those ids do not depend on the dictionary. `scripts/smoke_inference.py` therefore stores raw ids and decodes them with both dictionaries. With `SSL_HWD_Dict.txt`, all 8 samples decode to their ground truth. With `dictionary.txt`, every lowercase output is shifted by one letter (`living` -> `khuhmf`), and digits and uppercase are unchanged. **Selected: `SSL_HWD_Dict.txt`.** The authors have not confirmed this. The evidence is decisive for the lowercase block (ids 65-90 = a-z under `SSL_HWD_Dict.txt`). Digits (19-28) and uppercase (36-61) are the same under both dictionaries. Punctuation (ids 3-18, 29-35, 62-64) and the tail symbols (91-96: `{ } £ ¥ ° ₹`) were never emitted and remain untested. Under `dictionary.txt`, ids 91-96 would decode as `z { | } ~ £` instead.
- Upstream reads dictionaries with `open(path, "r")` and no encoding, so on Windows the non-ASCII symbols decode wrongly unless Python runs in UTF-8 mode. All runs therefore use `python -X utf8`, which matches the authors' Linux setup.
- Upstream output format: `vocab.indices2label` joins tokens with spaces (`l i v i n g`). The adapter also reports the tokens concatenated (`living`) for comparison with the ground truth. This is a display convention only.

## 3. Input preprocessing (test time)

- `comer/datamodule/dataset.py:24-28`: `ScaleToLimitRange(w_lo=16, w_hi=1024, h_lo=16, h_hi=256)`, then `torchvision ToTensor()`. Values are scaled to [0,1], with **no mean/std normalisation**. Scale augmentation runs only when `is_train and scale_aug`.
- `ScaleToLimitRange` (`transforms.py:9-42`): it asserts an aspect-ratio range, downscales if h>256 or w>1024, upscales if h<16 or w<16, and otherwise keeps the native size. All 8 samples were kept at native size.
- `datamodule.py:96-99`: images are read with PIL. `collate_fn` (`datamodule.py:125-149`) builds a 3-channel batch, zero-pads, and sets mask 1 = padding. Batch size 1 gives no padding and an all-zero mask.
- Channel order: RGB (PIL). The adapter calls `.convert("RGB")`, which equals upstream behaviour for RGB inputs and for broadcast grayscale.
- **Unverified assumption:** the script that converted SSL-HWD PNGs into upstream's `data.zip` (`img/*.jpg`, `caption.txt`) is not published. The adapter feeds PNGs at their stored polarity (dark ink on light paper) without inversion, which follows the code as written. The decodes are correct, which is consistent with this. JPEG re-encoding by the authors is not reproduced.

## 4. Decoding

`LitCoMER.approximate_joint_search` -> `CoMER.beam_search` -> `DecodeModel.beam_search` (`comer/utils/generation_utils.py`). This is a bi-directional (L2R and R2L) beam search followed by cross-direction rescoring. The beam settings come from the checkpoint hyperparameters: beam_size 10, max_len 200, alpha 1.0, early_stopping False, temperature 1.0. These match `config.yaml`. The adapter changes nothing here.

## 5. Checkpoint loading

- `torch.load(..., weights_only=True, map_location="cpu")` runs inside `safe_globals([ModelCheckpoint])`. A static `pickletools` scan found only `OrderedDict`, tensor-rebuild helpers and that one class reference, which serves as a dict key in callback state.
- Model built as `LitCoMER(**ckpt["hyper_parameters"])`, then `load_state_dict(ckpt["state_dict"], strict=True)`.
- **673 checkpoint keys, 673 model keys, 0 missing, 0 unexpected.** No prefix remapping was needed (`comer_model.` matches `LitCoMER`). All parameters are float32 on CPU, and `model.eval()` runs under `torch.inference_mode()`.
- Training state not loaded and kept separate: `optimizer_states`, `lr_schedulers`, `callbacks`, `epoch`, `global_step`, `hparams_name`, `pytorch-lightning_version`.

## 6. Runtime adapters (outside upstream; upstream bytes unchanged)

1. **Vocabulary**: `install_vocab()` runs upstream `vocab.py` unchanged. It confirms that the only failure is the missing `IIIT_Dict.txt`, keeps the upstream `CROHMEVocab` class and registers `CROHMEVocab(SSL_HWD_Dict.txt)` as `comer.datamodule.vocab` in `sys.modules`. If upstream ever imports cleanly, the adapter raises an error, so it cannot silently diverge.
2. **Backbone preload**: `Encoder.__init__` (`encoder.py:149-154`) calls `torch.load` on the hard-coded path `/home2/shree.mitra23m/CoMER/comer/model/BarlowTwins_HTR_backbone_step290000.pth`. During construction only, that exact path returns `None` and the matching `DenseNet.load_state_dict(None)` is skipped. The strict full-checkpoint load then overwrites every encoder weight (0 missing keys). No randomly initialised weight survives. Note: upstream still prints "Weights loaded successfully" at this point. **That message is misleading under the adapter.** The real load is the strict one reported above.
3. Version deviations: upstream targets PyTorch Lightning 1.4.9 (as recorded in the checkpoint) with old pins (`requirements.txt`: einops 0.3.0, opencv-python 4.5.4.60, and others). Python 3.11 has no wheels for that stack. We use torch 2.15.0+cpu, Lightning 2.6.6, torchmetrics 1.9.0 and opencv-python-headless 5.1.0.95, and keep einops 0.3.0 as pinned. The model and decoding code paths imported without changes. Training entry points (`train.py`, which uses Lightning 1.x CLI/DDP imports) were not run and are not expected to work on Lightning 2.x.

## 7. Paper/code observations

- `config.yaml` points at a RIMES 80% split (`/ssd_scratch/shree14/RIMES/splits/data_split_80/data.zip`), so it is not necessarily this checkpoint's configuration. Its model hyperparameters equal the checkpoint's.
- The checkpoint monitored `val_ExpRate` (CoMER's original metric name), while current `lit_comer.py` logs `val_WRR`. The checkpoint was therefore produced by an earlier code revision than the published one. Architecture keys still match exactly.
- `encoder.py:156-160` prints "Freezing" but sets `requires_grad = True` (unfrozen). This affects training only.
- Which downstream dataset this checkpoint was fine-tuned on is **unknown**. The vocabulary result is consistent with SSL-HWD.
