# M6 → M7 recommendation (evidence-ranked; nothing implemented yet)

## Primary contribution: adaptive text-height normalisation
Before the unchanged upstream transform, resize each crop isotropically, up or down, so that its estimated ink height lands in a target band. The band is chosen **on dev only**.

- **Supporting evidence:**
  - DX-B: upscaling small synthetic numbers (34 → 134 px) took exact from 0/8 to 5/8 and value exact from 0/8 to 5/8.
  - Upscaling genuine crops that start at about 70–80 px **hurt** them (CVL 4/8 → 0/8 at 4×).
  - Clean D1 crops ≥ 128 px are worse (CER 0.42) than 32–127 px crops (about 0.22).
  - Together these show a size-dependent optimum, so uniform upscaling is ruled out.
- **Complexity:** low. Otsu ink-height estimate plus one resize, a few dozen lines, training-free.
- **Cost:** CPU-cheap preprocessing. Larger inputs decode more slowly (M5: large GNHK crops took 2–8 s), so latency must be reported.
- **Risks:**
  - The band is tuned on small dev subsets, and the effect on synthetic numbers could be font-specific.
  - Ink-height estimates fail on near-empty or very noisy crops, so the method must fall back to the original image.
  - Downscaling large crops could drop thin punctuation.
- **Evaluation:**
  - choose the band from a small fixed grid on dev (D1, D4, D6) with M5 metrics;
  - freeze it, then run baseline vs improved once on the locked test split;
  - report paired ΔCER with cluster-bootstrap CIs per set, value exact, pair decisions and latency;
  - include an ablation (downscale only, upscale only).

## Secondary component (conditional): word segmentation for written amounts
- **Evidence:** oracle word crops at 2× reduced CER from 0.80 (full line 2×) to 0.46, with 8/49 words exact vs 0/49. Segmentation without the scale change gave much less (0.87 → 0.77).
- **Risk:** **automatic geometric segmentation failed** (0/8 lines matched the word count after two geometry fixes). Even with oracle boxes, 0/8 lines were fully correct, so written amounts would still rarely parse.
- **Recommendation:** treat it as an optional, separately ablated component. Only adopt it if a simple automatic segmenter, evaluated on dev, approaches oracle quality. Never report oracle results as the system.

## Not recommended
- **Foreground isolation by removing lines and borders.** DX-D showed no gain and a small loss at 2×.
- **Generic quality enhancement (contrast or denoising).** Mild corruptions barely matter. Severe contrast loss does hurt genuine text (CVL −16.7 pp), but that is a synthetic stress condition. It is a possible later ablation, not the main contribution.
- **Punctuation- or zero-specific post-correction.** Zero errors are rare, and punctuation n = 17 is too small. Correction would also break the frozen no-repair rule for amount values.

## Expected outcome (a hypothesis, not a result)
- Gains are most likely on small synthetic numeric fields.
- Little gain or no change is expected on genuine sets already in range.
- There is a possible gain on large D1 crops.
- Written synthetic amounts will probably still go to review, which keeps the amount pipeline review-heavy.
