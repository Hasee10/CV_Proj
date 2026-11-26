"""M3-A smoke inference for the released LoGo-HTR downstream checkpoint (CPU, no training).

Uses the unmodified upstream code in third_party/LoGoHTR. Two runtime adapters, both outside
upstream and documented in artifacts/M3_A/MODEL_INSPECTION.md:
  1. vocab.py defaults to IIIT_Dict.txt, which upstream does not ship. We run upstream
     vocab.py, keep its CROHMEVocab class, and build the vocab from a dictionary we name.
  2. Encoder.__init__ torch.loads a hard-coded Linux backbone path. During construction only,
     that one load is skipped; the strict full-checkpoint load then overwrites every weight.
Token ids do not depend on which 97-token dictionary is used to build the model, so every
prediction is decoded with BOTH candidate dictionaries and the raw ids are recorded.

Run (UTF-8 mode is required, as on the authors' Linux setup):
  .venv\\Scripts\\python.exe -X utf8 -I scripts\\smoke_inference.py --manifest data\\handwritten_examples\\manifest.json --out artifacts\\M3_B\\INFERENCE_RESULTS.json
  .venv\\Scripts\\python.exe -X utf8 -I scripts\\smoke_inference.py path\\to\\word.png --out artifacts\\<milestone>\\adhoc.json
--out is required and must not exist (protects earlier evidence). Unreadable images are reported
per sample; the warm-up uses the first readable image and its failure is recorded, not fatal.
"""
import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
import types
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "third_party" / "LoGoHTR"
DICT_DIR = UPSTREAM / "comer" / "datamodule"
CANDIDATE_DICTS = ["SSL_HWD_Dict.txt", "dictionary.txt"]  # the two 94-entry (97-token) dictionaries
CKPT = ROOT / "models" / "logo_htr" / "Downstream_Full_Model_Best.ckpt"
CKPT_SHA256 = "25db3a51f70a08cd5cbbf88409470bc4b37821aff95bc5ee6ab89e1e4298c432"
BACKBONE_PATH = "/home2/shree.mitra23m/CoMER/comer/model/BarlowTwins_HTR_backbone_step290000.pth"


def install_vocab(dict_name: str):
    """Run upstream vocab.py unchanged; its last line fails on the missing IIIT_Dict.txt."""
    path = DICT_DIR / "vocab.py"
    mod = types.ModuleType("comer.datamodule.vocab")
    mod.__file__ = str(path)
    try:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), mod.__dict__)
        raise RuntimeError("upstream vocab.py imported without error; adapter no longer needed")
    except FileNotFoundError as e:
        if "IIIT_Dict.txt" not in str(e):
            raise
    mod.vocab = mod.CROHMEVocab(str(DICT_DIR / dict_name))
    sys.modules["comer.datamodule.vocab"] = mod
    return mod


@contextmanager
def skip_backbone_preload():
    import torch
    real_load = torch.load

    def guarded(f, *a, **k):
        if f == BACKBONE_PATH:
            return None
        return real_load(f, *a, **k)

    from comer.model import encoder as enc
    real_lsd = enc.DenseNet.load_state_dict

    def lsd(self, sd, *a, **k):
        if sd is None:  # only the skipped backbone preload reaches here with None
            return None
        return real_lsd(self, sd, *a, **k)

    with mock.patch.object(torch, "load", guarded), mock.patch.object(enc.DenseNet, "load_state_dict", lsd):
        yield


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model(report: dict):
    import torch
    from pytorch_lightning.callbacks.model_checkpoint import ModelCheckpoint

    got = sha256(CKPT)
    if got != CKPT_SHA256:
        raise RuntimeError(f"checkpoint SHA-256 mismatch: {got}")
    # weights_only=True; the one non-tensor global is the callback-state dict key (a class ref).
    with torch.serialization.safe_globals([ModelCheckpoint]):
        ck = torch.load(CKPT, map_location="cpu", weights_only=True)

    from comer.lit_comer import LitCoMER
    hp = ck["hyper_parameters"]
    with skip_backbone_preload():
        model = LitCoMER(**hp)
    sd = ck["state_dict"]
    model_keys = set(model.state_dict().keys())
    res = model.load_state_dict(sd, strict=True)
    model.eval()
    report.update({
        "checkpoint_sha256": got,
        "checkpoint_top_level_keys": sorted(ck.keys()),
        "checkpoint_pl_version": ck.get("pytorch-lightning_version"),
        "checkpoint_epoch": ck.get("epoch"), "checkpoint_global_step": ck.get("global_step"),
        "checkpoint_monitor": {str(k.__name__): {kk: (float(vv) if hasattr(vv, "item") else vv)
                               for kk, vv in v.items()} for k, v in ck.get("callbacks", {}).items()},
        "hyper_parameters": hp,
        "state_dict_keys": len(sd), "model_state_keys": len(model_keys),
        "missing_keys": list(res.missing_keys), "unexpected_keys": list(res.unexpected_keys),
        "not_loaded_training_state": [k for k in ck if k not in ("state_dict", "hyper_parameters")],
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "parameter_count_encoder": sum(p.numel() for p in model.comer_model.encoder.parameters()),
        "parameter_count_decoder": sum(p.numel() for p in model.comer_model.decoder.parameters()),
        "buffer_count": sum(b.numel() for b in model.buffers()),
        "dtypes": sorted({str(p.dtype) for p in model.parameters()}),
        "device": str(next(model.parameters()).device),
        "vocab_size": int(sd["comer_model.decoder.proj.weight"].shape[0]),
    })
    return model


def preprocess(path: Path):
    """Upstream test-time path: PIL RGB -> ScaleToLimitRange(16..1024 w, 16..256 h) -> ToTensor."""
    import numpy as np
    import torch
    from PIL import Image
    from comer.datamodule.dataset import CROHMEDataset

    img = np.array(Image.open(path).convert("RGB"))
    x = CROHMEDataset([], is_train=False, scale_aug=False).transform(img)  # [3,H,W] in [0,1]
    mask = torch.zeros(1, x.shape[1], x.shape[2], dtype=torch.bool)  # batch of 1: no padding
    return x.unsqueeze(0), mask


def decode(ids, vocabs):
    return {name: "".join(v.indices2words(ids)) for name, v in vocabs.items()}


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


assert edit_distance("kitten", "sitting") == 3 and edit_distance("", "ab") == 2


def readable(path: Path, expected_sha256=None):
    """None if usable; else an error string. Manifest hash is enforced when the sample records one."""
    from PIL import Image
    if expected_sha256 and path.exists() and sha256(path) != expected_sha256:
        return "sha256 mismatch against manifest"
    try:
        with Image.open(path) as im:
            im.verify()
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="*")
    ap.add_argument("--manifest")
    ap.add_argument("--out", required=True, help="new JSON path; never reuse an earlier milestone's file")
    args = ap.parse_args()
    if not sys.flags.utf8_mode:
        print("ERROR: run with python -X utf8 (dictionaries contain UTF-8 symbols)", file=sys.stderr)
        return 2

    sys.path.insert(0, str(UPSTREAM))
    vmod = install_vocab(CANDIDATE_DICTS[0])
    vocabs = {d: vmod.CROHMEVocab(str(DICT_DIR / d)) for d in CANDIDATE_DICTS}
    assert all(len(v) == 97 for v in vocabs.values())

    import torch
    samples = []
    if args.manifest:
        samples = json.loads(Path(args.manifest).read_text(encoding="utf-8"))["samples"]
    samples += [{"id": f"U{i:02d}", "file": p, "ground_truth": None} for i, p in enumerate(args.images, 1)]
    if not samples:
        ap.error("give image paths or --manifest")

    report = {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
              "torch_threads": torch.get_num_threads(), "beam_note": "upstream bi-directional beam search, hparams from checkpoint"}
    t0 = time.perf_counter()
    model = load_model(report)
    report["model_load_seconds"] = round(time.perf_counter() - t0, 3)

    if Path(args.out).exists():
        print(f"ERROR: {args.out} exists; refusing to overwrite evidence", file=sys.stderr)
        return 2
    unreadable = {s["id"]: readable(ROOT / s["file"], s.get("sha256")) for s in samples}
    report["input_hash_checked"] = sum(bool(s.get("sha256")) for s in samples)
    report["unreadable_inputs"] = {k: v for k, v in unreadable.items() if v}
    results = []
    with torch.inference_mode():
        warm = next((s for s in samples if not unreadable[s["id"]]), None)
        try:
            x, m = preprocess(ROOT / warm["file"])
            t = time.perf_counter()
            model.approximate_joint_search(x, m)
            report["warmup_seconds"] = round(time.perf_counter() - t, 4)
            report["warmup_image"] = warm["file"]
        except Exception as e:  # warm-up failure must not hide per-sample results
            report["warmup_error"] = f"{type(e).__name__}: {e}" if warm else "no readable input"
        for s in samples:
            p = ROOT / s["file"]
            row = {"id": s["id"], "file": s["file"], "ground_truth": s.get("ground_truth"),
                   "condition": s.get("condition"), "category": s.get("category"), "error": unreadable[s["id"]]}
            if row["error"]:
                results.append(row)
                print(json.dumps({"id": s["id"], "error": row["error"]}))
                continue
            try:
                t = time.perf_counter()
                x, m = preprocess(p)
                hyp = model.approximate_joint_search(x, m)[0]
                row["latency_seconds"] = round(time.perf_counter() - t, 4)
                row["input_tensor_shape"] = list(x.shape)
                row["raw_token_ids"] = hyp.seq
                row["score"] = float(hyp.score)
                row["upstream_label_ssl_hwd_dict"] = vocabs["SSL_HWD_Dict.txt"].indices2label(hyp.seq)
                row["prediction_by_dict"] = decode(hyp.seq, vocabs)
                gt = row["ground_truth"]
                row["exact_match_by_dict"] = {k: (v == gt if gt is not None else None)
                                              for k, v in row["prediction_by_dict"].items()}
                pred = row["prediction_by_dict"]["SSL_HWD_Dict.txt"]
                # labelled view only: upstream strips the space line to "", so id 3 never shows as a space
                row["view_space_token_as_space"] = "".join(
                    " " if i == 3 else vocabs["SSL_HWD_Dict.txt"].idx2word[i] for i in hyp.seq)
                row["space_token_emitted"] = 3 in hyp.seq
                if gt is not None:
                    row["char_edit_distance"] = edit_distance(pred, gt)
                    row["cer"] = round(row["char_edit_distance"] / len(gt), 4)
            except Exception as e:  # record and continue: every sample must be reported
                row["error"] = f"{type(e).__name__}: {e}"
            results.append(row)
            print(json.dumps({k: row.get(k) for k in ("id", "ground_truth", "prediction_by_dict", "latency_seconds", "error")},
                             ensure_ascii=False))

    lat = [r["latency_seconds"] for r in results if r.get("latency_seconds") is not None]
    report["latency_includes"] = "preprocess + encoder + bi-directional beam search (beam 10) + rescoring; batch size 1; excludes model load and warm-up"
    report["latency_median_seconds"] = statistics.median(lat) if lat else None
    report["latency_min_max_seconds"] = [min(lat), max(lat)] if lat else None
    report["results"] = results
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0 if not any(r["error"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
