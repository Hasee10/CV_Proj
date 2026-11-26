# Formal baseline definition (fixed for M5 onward)

## Recogniser (B0)
| Component | Value |
|---|---|
| Model | official LoGo-HTR full downstream checkpoint `Downstream_Full_Model_Best.ckpt`, HF `Shree10/LoGo-HTR` @ `64439ca9…`, SHA-256 `25db3a51…c432` |
| Code | upstream `shreemitra/LoGoHTR` @ `9eaea5fe…`, unmodified; runtime adapters only (vocab path, backbone pre-load skip), see `artifacts/M3_A/MODEL_INSPECTION.md` |
| Vocabulary | `SSL_HWD_Dict.txt` (97 tokens; established empirically in M3-A) |
| Preprocessing | upstream test path: RGB, `ScaleToLimitRange(w 16–1024, h 16–256)`, `ToTensor` (no normalisation), batch 1 |
| Decoding | upstream bidirectional beam search, beam 10, max_len 200, alpha 1.0 (checkpoint hyper-parameters) |
| Weights | frozen, `eval()`, `torch.inference_mode()`, CPU float32, no training of any kind |
| Output | raw token ids + concatenated decode; id 3 (stripped space) decodes to `""`; **no** post-correction |
| Entry point | `scripts/smoke_inference.py --manifest … --out <new path>` (input hashes enforced) |

## Cheque-level baseline pipeline (P0)
1. **Region extraction:** template-registered crops from the custom sheets (ArUco homography plus fixed box coordinates). This is a known-layout assumption shared by baseline and improved systems. It is **not** automatic cheque-field detection on arbitrary cheques, which is not implemented.
2. **Recognition:** B0 on the numeric box and on the words box (full line, no segmentation).
3. **Parsing:** the frozen level-B rules in `EVALUATION_PROTOCOL.md` (`numeric_value`, `words_value`). Unspaced text is not segmented.
4. **Decision:** `decide()` (accept / flag / review).

Expected consequence, known from M3-B and stated in advance: B0 rarely emits spaces, so most written amounts will be unparseable and P0 will route many pairs to **review**. This is a documented baseline limitation, not an implementation error.

## Fairness rules for the improved system
- It uses the same checkpoint, vocabulary, decoding settings, crops, parser and decision rule unless the change *is* the proposed improvement. Each change is then ablated separately against B0/P0.
- It gets no ground truth, prompt text or amount list at inference time, and no information the baseline lacks (for example, the improved system may not read the printed prompt).
- Its parameters are selected on dev only. Test is evaluated once.
- Oracle (manual or annotation) crops and template-registered crops are reported as such, and never described as automatic segmentation.

## Not claimed
Automatic full-cheque verification, signature verification and forgery or tampering detection are not implemented and are outside the current scope. The broader approved topic mentions them, and the report must state that the project covers handwritten amount verification only.

---
## Amendment M4-ONLINE (2026-11-26): region extraction for the selected datasets
The recogniser B0 is unchanged (checkpoint, vocabulary, preprocessing, beam search). The cheque-level pipeline P0 now uses:
1. **Region extraction (oracle, shared by baseline and improved):**
   - D4 CVL uses the dataset-provided single-string images;
   - D1 and D5 GNHK use the official word-polygon bounding boxes;
   - D6 synthetic cheques use one fixed box per template and field (`template_oracle_box`, in `scripts/build_online_benchmarks.py`).
   - None of these is automatic cheque-field detection, which is not implemented.
   - The template id is known from the dataset, not inferred.
   - The ArUco custom sheets are retired from the required pipeline.
2. Recognition, parsing and decision are unchanged (B0, the frozen level-B grammars, `decide()`).
3. Genuine sets (D1, D4, D5) and the synthetic set (D6) are always reported separately. D6 results describe font-rendered text, not handwriting.
