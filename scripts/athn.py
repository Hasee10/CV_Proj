"""Adaptive Text-Height Normalisation (ATHN): training-free, image-only preprocessing before unchanged LoGo-HTR.

1. Estimate text height from the image alone: Otsu ink mask; long printed lines (>= 50% of width or height) removed;
   8-connected components filtered to character/word-like blobs; text height = 80th percentile of their heights.
   This is an estimate, not a measurement; it fails on empty, near-uniform or very noisy crops (-> identity).
2. If the estimate lies inside [band_lo, band_hi] keep the image (identity path). Otherwise resize isotropically by
   target / estimate, clamped to [min_scale, max_scale] and so that the result stays within the upstream caps
   (h <= 256, w <= 1024) and minimum (16 px). INTER_CUBIC to enlarge, INTER_AREA to shrink. Aspect ratio kept.
No ground truth, field labels or dataset names are used; only pixels.
"""
import cv2
import numpy as np

UP_H, UP_W, MIN_SIDE = 256, 1024, 16


def estimate_text_height(rgb: np.ndarray):
    """Returns (height_px or None, info dict)."""
    if rgb is None or rgb.ndim != 3 or min(rgb.shape[:2]) < 4:
        return None, {"reason": "invalid_image"}
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    if grey.std() < 2:
        return None, {"reason": "uniform_image"}
    _, ink = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    frac = float((ink > 0).mean())
    if not 0.002 <= frac <= 0.6:
        return None, {"reason": "ink_fraction_out_of_range", "ink_fraction": round(frac, 4)}
    h, w = grey.shape
    lines = cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 2), 1))) | \
        cv2.morphologyEx(ink, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(3, h // 2))))
    ink = cv2.bitwise_and(ink, cv2.bitwise_not(lines))
    n, _, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    min_area = max(4, int(1e-4 * h * w))
    hs = [int(s[cv2.CC_STAT_HEIGHT]) for s in stats[1:]
          if s[cv2.CC_STAT_AREA] >= min_area and s[cv2.CC_STAT_HEIGHT] >= 3
          and s[cv2.CC_STAT_HEIGHT] <= 0.95 * h and s[cv2.CC_STAT_WIDTH] <= 0.9 * w]
    if not hs:
        return None, {"reason": "no_text_components"}
    return float(np.percentile(hs, 80)), {"components": len(hs), "ink_fraction": round(frac, 4)}


def apply(rgb: np.ndarray, cfg: dict):
    """Returns (image, meta). cfg: band_lo, band_hi, target, min_scale, max_scale."""
    est, info = estimate_text_height(rgb)
    h, w = rgb.shape[:2]
    meta = {"method": "ATHN", "estimated_text_height": est, **info, "input_hw": [h, w], "scale": 1.0,
            "interpolation": None, "applied": False}
    if est is None or cfg["band_lo"] <= est <= cfg["band_hi"]:
        meta["path"] = "identity" if est is not None else "identity_fallback"
        return rgb, meta
    s = min(max(cfg["target"] / est, cfg["min_scale"]), cfg["max_scale"])
    s = min(s, UP_H / h, UP_W / w) if s > 1 else s          # enlarging beyond the upstream caps would be undone
    s = max(s, MIN_SIDE / h, MIN_SIDE / w)
    if abs(s - 1) < 0.05:
        meta["path"] = "identity_small_change"
        return rgb, meta
    interp = cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA
    out = cv2.resize(rgb, (max(1, round(w * s)), max(1, round(h * s))), interpolation=interp)
    meta.update(scale=round(s, 4), interpolation="INTER_CUBIC" if s > 1 else "INTER_AREA", applied=True,
                path="resized", output_hw=list(out.shape[:2]))
    return out, meta


def _selftest():
    img = np.full((40, 160, 3), 255, np.uint8)
    cv2.putText(img, "3083", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    est, _ = estimate_text_height(img)
    assert est is not None and 10 <= est <= 30, est
    cfg = {"band_lo": 40, "band_hi": 80, "target": 56, "min_scale": 0.5, "max_scale": 4.0}
    out, meta = apply(img, cfg)
    assert meta["applied"] and out.shape[0] > img.shape[0] and abs(out.shape[1] / out.shape[0] - 4) < 0.1
    assert apply(np.full((40, 160, 3), 255, np.uint8), cfg)[1]["path"] == "identity_fallback"
    big = cv2.resize(img, None, fx=6, fy=6)
    assert apply(big, cfg)[0].shape[0] < big.shape[0]
    print("athn self-test passed")


if __name__ == "__main__":
    _selftest()
