# ChequeVerify visual direction

Selected by the project owner on 27 November 2026. This file records the design decisions; it is not a claim that later milestones are implemented.

## Sequence and placement

1. Opening: volumetric light inspired by https://cullenwebber.github.io/three-volumetric-light/. A procedural document is the focal point, replacing the reference's hand and character. Immediate access to the dashboard; no mandatory splash delay or fabricated progress. Original geometry and shader code, no upstream assets or source copied.
2. Dashboard: quiet paper surfaces, ink typography and real backend status. No running 3D scene inside task views.
3. Verification / recognition: precise, accessible image selection and faithful results in F2/F3. Originals uploaded unchanged. No perspective transformations on the ROI drawing surface.
4. Research / methodology: LeafThrough (https://dmtrbrl.github.io/leafthrough/) is locked as a later reader treatment for a concise research/sample booklet. Ordinary accessible text and previous/next controls remain available. Never use page turning for the required result tables. Upstream repository https://github.com/dmtrbrl/leafthrough declares MIT; preserve attribution if integrated.
5. Research transition: a bounded procedural wave/cluster study, illustrative only. The owner supplied link text https://tympanus.net/Tutorials/3DCluster/ pointing to https://projects.arkon.digital/threejs/wavy-cubes/. Both are retained as references; current direction uses the destination's wave grid. Do not treat the cube positions as actual model activations or benchmark data. Resolve the exact variant before this section is built.

## Palette

| Role | Colour |
| --- | --- |
| Ink / intro | #101e28 |
| Workspace / paper | #f5f6f4 |
| Panel | #ffffff |
| Accent | #24685f |
| Secondary text | #52626b |
| Rule | #dce1df |

Terminal screenshot reference: restrained light surfaces, fine outlines and a compact identity. Do not reproduce its logo. Teal is the primary accent; amber indicates unavailable/error attention. Status always includes text.

## Implementation constraints

React, strict TypeScript, Vite, Tailwind, Lucide, React Router, Vitest. Three.js is lazy loaded only on the introduction route. No Blender or paid tools required. Existing backend stays on port 8000; Vite stays on 5173.

Intro renderer uses a low-power context, DPR capped at 1.25, 30 fps maximum and a 24-step light integral. It pauses when hidden/offscreen and disposes resources on unmount. Reduced-motion renders a still. WebGL failure leaves the CSS atmosphere and all navigation usable. Performance on the user's actual GPU still needs subjective review.

Only F1 is implemented now. Leafthrough and cubes remain scoped; recognition and benchmark routes are explicitly pending. Integration quality and truthful research presentation take precedence over additional effects.
