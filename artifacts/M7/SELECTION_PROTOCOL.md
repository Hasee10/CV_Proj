# M7 selection protocol (frozen before any M7 inference; dev split only)

## Justification for the candidates (measured, no predictions used here)
- **Text height** (`scripts/athn.py` estimator, in effective pixels after the upstream transform; dev medians):
  - D1: 45 px (p10–p90 16–90);
  - D4: 45 px (25–60);
  - D6 numeric: 14 px (12–16);
  - D6 words: 12 px (10–15).
- **M6 DX-B results:**
  - synthetic numbers were best at 4×, about 50 px text (0/8 → 5/8 exact);
  - CVL degraded at 2×, about 90 px text (4/8 → 1/8);
  - D1 crops ≥ 128 px were worse than mid-sized ones.

Together these point to a target of about 40–56 px, with genuine text left mostly untouched.

## Configurations (fixed list; no further candidates will be added)
| id | method | band_lo | band_hi | target | min_scale | max_scale | role |
|---|---|---|---|---|---|---|---|
| B0 | unchanged baseline (M5 predictions reused) | - | - | - | - | - | reference |
| B1 | uniform 2× enlargement of every crop | - | - | - | 2.0 | 2.0 | ablation (no adaptivity) |
| P1-A | ATHN | 24 | 72 | 48 | 0.5 | 4.0 | candidate |
| P1-B | ATHN | 32 | 64 | 48 | 0.5 | 4.0 | candidate (tighter band) |
| P1-C | ATHN | 20 | 90 | 40 | 0.5 | 4.0 | candidate (conservative) |
| P1-D | ATHN, enlarge only | 24 | ∞ | 48 | 1.0 | 4.0 | ablation (no shrinking) |

All configurations share the same checkpoint, dictionary, upstream transform and beam search. ATHN sees pixels only.

## Data
- All dev entries of D1, D4, D5 and D6: 251, of which 245 are recognition-eligible.
- Dev amount pairs: 2 GNHK and 72 synthetic.
- D5 (3 crops) is reported but never used for selection.

## Primary objective
D6 numeric **amount-value exact** (dev, n = 35). Secondary: D6 pairs with a correct automatic decision (matches accepted plus mismatches flagged).

## Guardrails (all must hold vs B0 on dev)
1. D1 aggregate CER increase ≤ 0.02 **and** D1 exact drop ≤ 2 samples.
2. D4 aggregate CER increase ≤ 0.02 **and** D4 exact drop ≤ 2 **and** D4 value-exact drop ≤ 2.
3. Incorrect acceptance rate on D6 pairs ≤ 0.10.
4. Median latency over all dev entries ≤ 0.90 s (3× B0's 0.29 s).
5. The method must not route every pair to review **unless** the baseline already does. A remaining all-review outcome is reported, not hidden.

## Decision rule
1. Keep the P1 candidates that pass all guardrails.
2. Pick the highest primary objective. Ties are broken by:
   1. the higher secondary objective;
   2. the lower combined D1 + D4 CER;
   3. the more conservative band (fewer genuine crops resized);
   4. id order.
3. **Success** requires the chosen candidate's primary objective to exceed B0 by at least 3 samples (B0 = 0/35). Otherwise M7 is recorded as a **negative result**, and the backend keeps the baseline as its main mode.
4. B1 and P1-D are ablations and cannot be selected.

## Conditional segmentation (P2)
After P1 is chosen, P2 = chosen P1 plus the M6 A2 geometric word segmentation, applied only to **written-amount** fields (field type is a user-supplied input in the product; not a dataset rule).
- Evaluate on D6 words dev (37).
- Adopt P2 only if, compared with P1 on the same crops, it gives **≥ 3 more lines whose written value parses and is correct** and lower CER.
- Otherwise reject it and document the negative result.
