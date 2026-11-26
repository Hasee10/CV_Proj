"""Frozen synthetic stress-test corruptions (M4 protocol; generation runs in M6, not now).

One corruption per variant, applied to the clean RGB uint8 crop; output is lossless PNG with the
same size. Severity parameters are fixed here and were NOT tuned on model performance.
Per-variant seed = first 8 hex of sha256("{sample_id}|{corruption}|{level}|{BASE_SEED}").
Naming: {sample_id}__{corruption}_s{level}.png ; manifest rows carry parent_id and the parent's split.
Usage (M6): .venv\\Scripts\\python.exe -I scripts\\stress_corrupt.py MANIFEST.json --split dev --out-dir DIR
Self-test:  .venv\\Scripts\\python.exe -I scripts\\stress_corrupt.py --selftest
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BASE_SEED = 20261126
# level -> parameter; H = image height in pixels
PARAMS = {
    "lowres": {1: 0.5, 2: 0.35, 3: 0.25},      # downscale factor (INTER_AREA), then back to original size (INTER_LINEAR)
    "blur": {1: 0.01, 2: 0.02, 3: 0.035},      # Gaussian sigma = p * H (kernel auto from sigma)
    "illum": {1: 0.3, 2: 0.5, 3: 0.7},         # I * (1 - a * ramp); linear ramp 0..1 along a seeded direction
    "contrast": {1: 0.6, 2: 0.4, 3: 0.25},     # mean + c * (I - mean), mean over all pixels
    "noise": {1: 8.0, 2: 16.0, 3: 32.0},       # additive Gaussian, sigma on 0..255, per pixel and channel
}


def seed_for(sample_id: str, corruption: str, level: int) -> int:
    return int(hashlib.sha256(f"{sample_id}|{corruption}|{level}|{BASE_SEED}".encode()).hexdigest()[:8], 16)


def corrupt(img: np.ndarray, corruption: str, level: int, seed: int) -> np.ndarray:
    p, h, w = PARAMS[corruption][level], img.shape[0], img.shape[1]
    x = img.astype(np.float32)
    rng = np.random.default_rng(seed)
    if corruption == "lowres":
        small = cv2.resize(img, (max(1, round(w * p)), max(1, round(h * p))), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    if corruption == "blur":
        x = cv2.GaussianBlur(x, (0, 0), sigmaX=max(0.3, p * h))
    elif corruption == "illum":
        ang = rng.uniform(0, 2 * np.pi)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = xx * np.cos(ang) + yy * np.sin(ang)
        r = (r - r.min()) / max(1e-6, r.max() - r.min())
        x = x * (1 - p * r)[..., None]
    elif corruption == "contrast":
        x = x.mean() + p * (x - x.mean())
    elif corruption == "noise":
        x = x + rng.normal(0, p, x.shape)
    return np.clip(np.rint(x), 0, 255).astype(np.uint8)


def selftest():
    rng = np.random.default_rng(0)
    img = np.full((60, 200, 3), 230, np.uint8)
    img[20:40, 30:170] = rng.integers(0, 80, (20, 140, 3))
    for c in PARAMS:
        for lv in PARAMS[c]:
            a = corrupt(img, c, lv, seed_for("T", c, lv))
            assert a.shape == img.shape and a.dtype == np.uint8
            assert np.array_equal(a, corrupt(img, c, lv, seed_for("T", c, lv))), "not deterministic"
    diffs = [np.abs(corrupt(img, "noise", lv, 1).astype(int) - img).mean() for lv in (1, 2, 3)]
    assert diffs[0] < diffs[1] < diffs[2], "noise severity not monotonic"
    stds = [corrupt(img, "contrast", lv, 1).std() for lv in (1, 2, 3)]
    assert stds[0] > stds[1] > stds[2], "contrast severity not monotonic"
    print("stress_corrupt self-test passed")


def generate(manifest, split, out_dir, root=ROOT):
    """Write paired variants for one split. Refuses a non-empty out_dir; validates every parent's sha256,
    image read and image write; copies all parent metadata except file/sha256. Returns (rows, problems)."""
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        return [], [f"{out} not empty; refusing to overwrite"]
    src = json.loads(Path(manifest).read_text(encoding="utf-8"))
    parents = [s for s in src["samples"] if not split or s.get("split") == split]
    problems = []
    for s in parents:
        f = root / s["file"]
        if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != s.get("sha256"):
            problems.append(f"{s['id']}: source missing or sha256 mismatch")
    if problems or not parents:
        return [], problems or ["no source samples selected"]
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in parents:
        raw = cv2.imread(str(root / s["file"]), cv2.IMREAD_COLOR)
        if raw is None:
            problems.append(f"{s['id']}: unreadable")
            continue
        img = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
        meta = {k: v for k, v in s.items() if k not in ("id", "file", "sha256")}
        for c in PARAMS:
            for lv in PARAMS[c]:
                vid = f"{s['id']}__{c}_s{lv}"
                path = out / f"{vid}.png"
                if not cv2.imwrite(str(path), cv2.cvtColor(corrupt(img, c, lv, seed_for(s["id"], c, lv)), cv2.COLOR_RGB2BGR)):
                    problems.append(f"{vid}: write failed")
                    continue
                rows.append({**meta, "id": vid, "parent_id": s["id"], "parent_sha256": s["sha256"], "corruption": c,
                             "level": lv, "param": PARAMS[c][lv], "seed": seed_for(s["id"], c, lv),
                             "file": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (out / "manifest.json").write_text(json.dumps({"source_manifest": str(manifest), "params": PARAMS, "base_seed": BASE_SEED,
                                                   "problems": problems, "samples": rows}, indent=2), encoding="utf-8")
    return rows, problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--split")
    ap.add_argument("--out-dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    rows, problems = generate(a.manifest, a.split, a.out_dir)
    print(f"{len(rows)} variants -> {a.out_dir}; problems: {problems or 'none'}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
