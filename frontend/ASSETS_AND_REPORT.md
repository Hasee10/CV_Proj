# Brand and visual report — 27 November 2026

The opening restores Cullen Webber's rigged hand and volumetric-light renderer, adapted locally from upstream commit `28b2103f1ce0403eacbe53c4ea53790b8905705a`. The hand uses its original animated finger/wrist bones; only the floating symbol geometry is replaced with the ChequeVerify C/check. Original ASCII shading, glow, dust, shadows, camera response and beam composition remain. Source hashes and adaptation notes are in `src/light-study/UPSTREAM.json`. Three.js 0.182.0 matches the upstream renderer's shadow-depth requirements. Assets and Draco decoding are served locally. The rejected still hand plate is no longer part of the application.

## Assets

- `public/brand/mark-3d.png`: transparent 1280×1280 rendered brand mark. An angular C bracket and check, with silver-green faces, forest-green sidewalls and a lavender edge reflection. Used in the shared Brand component, favicon and report cover.
- `public/brand/mark.svg` and `mark-flat.png`: canonical silhouette and reference. The new extruded floating geometry uses the same C/check silhouette with the reference ASCII material.
- `public/light-study/arm_bones.glb`: the reference rigged hand, with its original animated finger/wrist skeleton.
- `public/light-study/draco/`: local Three.js Draco decoders; source notices retained.
- `public/field-report/1.png` through `6.png`: six 1200×1600 pages, 3:4 width/height ratio. A new cover, actual field crops, raw baseline output, same-input ATHN comparison, three recorded decisions and genuine/synthetic research figures.
- `public/field-report/provenance.json`: capture run and response sources. All scientific content comes from `public/results/20261127T081154Z-cbb492/`.
- `public/fonts/Manrope.ttf`: self-hosted variable Manrope font, distributed with its SIL Open Font License. Source: https://github.com/google/fonts/tree/main/ofl/manrope. No runtime font service.

The old repeating cheque-outline SVG pages are no longer used. Original input crops are magnified for publication; no OCR output or source image has been corrected. Raw response files and research metrics remain unchanged.

## Rebuild the report

From the repository root:

```powershell
.\.venv\Scripts\python.exe -X utf8 frontend/scripts/create-report.py
```

Requires Pillow in the existing environment. It lays out actual stored input crops and values, creates the six PNGs, and generates `src/generated/report.ts` so the accessible transcript contains the same evidence. It makes no API requests and runs no inference. The LeafThrough page aspect is `1600 / 1200`; renderer DPR is capped at 2, with reduced grain, no show-through, and direct PNG links for close reading.

## Generation prompts

The rendered logo and the now-retired still hand plate were produced using the built-in image generation tool. The current animated hand and beam are adapted from the attributed reference, not image generation. The mark's reference was the project-created `mark-flat.png`. The prompts were:

**Retired hand plate (no longer used):** Create a premium cinematic photographic background plate for a computer-vision website introduction, landscape 16:9 at high resolution. A realistic human right hand and forearm, palm upward, fingers relaxed and gently cupped, occupying the lower middle and right, forearm entering from the lower right edge. The open space above the middle of the palm must be empty so we can place an interactive 3D logo there in code. Black and extremely dark teal atmospheric studio background. A dramatic broad white volumetric light beam comes diagonally from the left through subtle mist, illuminating the palm and finger edges, with a very subtle warm gold rim. Restrained optical grain, beautiful anatomical detail, sculptural photographic lighting. Hand fingertips around the horizontal center, palm centered near 60% across and 65% down. Keep the upper center half empty and dark for a luminous emblem. No letters, words, symbols, logos, holograms, particles shaped into objects, borders, captions, UI, watermarks, or bank imagery. This is an original atmospheric background, inspired by volumetric-light art direction, not a screenshot. Elegant and photorealistic, no plastic CGI hand.

**3D mark:** Create a beautifully finished 3D logo asset using the supplied flat mint emblem as the exact silhouette reference. Preserve both parts exactly: an angular open C bracket at left combined with a rising checkmark at right, including the open negative space, lengths and proportions. Do not add letters, circles, framing, text or extra symbols. Make this same mark a solid finely bevelled extruded object, deep polished forest-green metal with pale silver-green front faces and a restrained lavender reflected edge. Three-quarter front view with slight yaw so the right sidewalls and substantial depth are visible, the glyph still reads clearly. Premium industrial design product rendering, controlled softbox lighting, crisp clean edges, delicate specular highlights, believable ambient occlusion, no exaggerated reflections, no plastic, no decorative pedestal. Entire object centered and fully visible with generous empty margin. Genuinely transparent background, no background colour or scenery, no shadow plane. Square composition at high resolution, useful as a website brand asset and a publication cover illustration.

## Interaction and scope

The opening contains the real animated hand/beam scene and one arrow button, with an accessible Enter label. A translucent blurred surface now backs the hero copy so tile seams do not cross the lettering. The removed text includes the header wordmark, Skip caption, introductory headings, taglines, on-screen credit/status line, hero movement instruction and hero footer labels. Credits remain available in the landing footer. The book's long instruction sentence was removed; arrow controls, text version and page PNG access remain.

The landing sequence is opening → tiled hero → workflow with a recorded model example → visual field report → genuine/synthetic research evidence → workspace handoff. Workflow and research sections load existing saved responses only. There is no inference on page load. Application typography uses Manrope throughout, with revised heading spacing and responsive sizes.

The existing custom-upload/ROI-editing limitations remain as documented in RESULTS_HANDOVER.md. This revision changes branding, content and presentation only.
