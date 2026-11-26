# M4 synthetic stress-test protocol (frozen; run in M6)

The implementation is `scripts/stress_corrupt.py`. Its self-test passes: shape and dtype are preserved, output is deterministic per seed, and noise and contrast severity are monotonic. No variants have been generated yet.

| Corruption | Transformation on the clean RGB uint8 crop (H = height in px) | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| `lowres` | downscale by factor *f* (`INTER_AREA`), upscale back to the original size (`INTER_LINEAR`) | f = 0.5 | 0.35 | 0.25 |
| `blur` | Gaussian blur, σ = *p*·H (kernel derived from σ, min σ 0.3) | p = 0.01 | 0.02 | 0.035 |
| `illum` | I·(1 − a·r), where r is a linear ramp 0→1 along a seeded random direction | a = 0.3 | 0.5 | 0.7 |
| `contrast` | μ + c·(I − μ), with μ the mean over all pixels | c = 0.6 | 0.4 | 0.25 |
| `noise` | I + N(0, σ²) per pixel and channel, on the 0–255 scale | σ = 8 | 16 | 32 |

- **Order:** read the clean crop, apply exactly one corruption, round, clip to 0–255, then save as lossless PNG at the same size. Corruptions are never chained.
- **Seeds:** `int(sha256("{sample_id}|{corruption}|{level}|20261126")[:8], 16)`, so the same variant is produced on every run.
- **Naming and lineage:** `{sample_id}__{corruption}_s{level}.png`. Each manifest row records `parent_id`, `corruption`, `level`, `param`, `seed`, `sha256` and the parent's `split`. The clean parent is always evaluated alongside its variants (paired).
- **Scale:** 15 variants per clean sample. For example, GNHK dev 80 gives 1,200 images and GNHK test 160 gives 2,400. These are generated on demand into an explicit, empty output folder (`--out-dir`) and are not committed.
- **Severity choice:** set by visual plausibility for phone photos (mild to strong) before any inference. **The parameters were not tuned on model performance**, and they will not be changed after M6 results are seen.
- **Transcription safety:** none of the transforms moves, adds or removes strokes, so the ground truth is unchanged. At level 3, `lowres` and `blur` can make thin punctuation such as `.` and `,` illegible even to a human. In those cases the sample stays in the set, but a human-legibility check on dev is recorded before conclusions are drawn.
- **Risk:** synthetic corruptions are uniform and independent, unlike real photos, where blur, shadow and JPEG artefacts co-occur. Synthetic results are reported **separately** from naturally challenging photographed handwriting (D2, M3-B full photos) and are never pooled with them.

---
## Amendment M4-AUDIT (2026-11-26)
- **Generation safeguards** (`generate()`):
  - every parent's SHA-256 is checked before anything is written, and a mismatch aborts with no output;
  - unreadable parents and failed writes are reported;
  - all parent metadata (pair_id, category, writer_id, split, ...) is copied and `parent_id` and `parent_sha256` are added;
  - a non-empty output folder is refused.
  - `validate_manifest.py` verifies lineage when parent and variant manifests are validated together.
- **Legibility.** Severe levels can erase visible character information, especially `.` and `,`. The source transcription stays the reference label, but human legibility may be reduced. Results are reported per level, and synthetic results are never pooled with naturally difficult photographs.
- **Runtime estimate (before M6).** These are estimates from measured latencies, not measurements of these sets:
  - M3-A in-domain words of about 40-80 px height: median 0.14 s. M3-B crops of 145-256 px height: median 1.11 s. The M3-B multiword line: 6.1 s.
  - GNHK crops have a median height of 103 px. Clean pass: 240 x (0.14-1.11 s), about 1-5 min. Stress: 3,600 x (0.14-1.11 s), about 8-67 min.
  - Custom set, 5 writers, 210 crops: numeric about 105 x 0.3-1.2 s, words lines about 105 x 1-6 s, so about 3-13 min clean. Its stress set (3,150 variants) could take up to about 1-4 h, and will be run in the background.
  - M5 will measure the real per-set latency first. **The sample count will not be cut to fit time, and easy samples will not be selected.** If a run is infeasible, that will be reported as a limitation.
