# Visual correction verification - 27 November 2026

The earlier F1 acceptance report is historical. This revision implements all three selected visual placements; it does not add F2-F4 application features.

## Observed in the browser

- Cullen Webber's original hosted volumetric light/hand scene displays in the entry, on desktop and mobile. Enter and keyboard Skip lead to the landing; the iframe is removed afterwards (observed iframe count 0).
- The hero renders a local, animated shell of extruded triangular facets. Pointer drag input exercised. No wave-grid substitute. At 768px the hero was changed to a stacked composition after overlap was found; final tablet screenshot confirms separation.
- Actual LeafThrough 0.1.8 reader displays the original local cover. Next advances to pages 2-3 on desktop and page 2 on mobile; labels and Previous state update. Keyboard Enter activates Next. Non-3D mode and complete-text disclosure checked. The plain-text link opens the disclosure.
- Landing-to-dashboard navigation still displays live Model ready and the real LoGo-HTR model information.
- Inspected at 1440x900, 768x1024 and 390x844. Tablet/mobile document widths did not exceed their viewport widths. No console errors/warnings appeared during the healthy sequence review.
- Entry replay/enter clears the old section fragment so entry into the landing starts at the hero.

## Commands

- npm run build: PASS, includes strict TypeScript check; final build 11.47s. Shared Three.js chunk 493.11kB, cluster module 3.73kB, reader module 87.16kB (uncompressed).
- npm test: 16/16 existing API/status tests PASS. New visual interactions were manually checked in the browser, not covered by a new automated browser suite.
- .venv/Scripts/python.exe scripts/guard.py --verify: all 1174 frozen files match.
- git diff --check: PASS.

## Screenshots

Outside Git at C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-visual-revision/:

- 01-light-entry.jpg
- 02-cluster-hero.jpg
- 03-field-notes-cover.jpg
- 04-field-notes-spread.jpg
- 05-mobile-hero.jpg
- 06-mobile-reader.jpg
- 07-tablet-hero.jpg

## Limits

The entry is a credited external embed and needs internet; it is not self-hosted or student-authored. The cluster and booklet are local. Reduced-motion paths are implemented but were not browser-emulated. No GPU performance benchmark, automated accessibility audit, or full recognition end-to-end suite was run. No backend, frozen research, data or model changes.

Full source/asset attribution: VISUAL_CREDITS.md and public/leafthrough-license.txt. Booklet images are generated original SVGs with committed source.

## Subsequent owner-requested wave replacement

The spherical cluster described above has now been replaced by a full-hero tiled wave surface referencing https://projects.arkon.digital/threejs/wavy-cubes/. Independent local instanced Three.js cubes, thin seams, gentle height/tilt waves, and a lavender pointer highlight. Pale surface and dark typography extend across the entire hero; no separate right-hand object remains.

Type-check/build PASS (10.23s); existing unit tests 16/16 PASS; all 1174 frozen hashes match. Browser inspected at 1440x900 and 390x844; pointer response exercised, no console errors/warnings. Mobile document width does not exceed its viewport. Latest screenshots: C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-wave-hero/desktop.jpg and mobile.jpg. No new automated visual tests or GPU benchmark. Credits and current design direction updated. Entry light experience and LeafThrough reader retain their existing implementations.

### Raised tile refinement

Owner requested more visible 3D depth. Flat boxes replaced with bevelled RoundedBoxGeometry, thicker sidewalls, a slightly elevated viewing angle, stronger height variation and real 1024px soft directional shadow maps. Instanced tiles cast/receive shadows over a recessed backing plane. Brighter fill and a quiet wash behind copy preserve readability; pointer coordinates now raycast to the tilted view. Existing 30fps/DPR caps, hidden/offscreen pause and reduced-motion handling remain.

Strict type-check/build passed. Manually reviewed at 1440x900 and 390x844; no console errors/warnings and no mobile horizontal overflow. Screenshots: C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-raised-tiles/desktop.jpg and mobile.jpg. No new unit tests for this visual-only refinement and no measured GPU benchmark. All 1174 frozen files match.

### Cursor-only relief, larger typography and workspace revision

Removed time-driven waves, resting tile tilt and continuous idle rendering. Tile relief is localized to movement, then eases to zero after movement stops (140ms inactivity threshold), even with the pointer still inside. At rest all tile positions have z=0 and rotation=0. Rendering stops once settled and resumes for pointer movement, layout or visibility changes. Reduced-motion remains static.

Raised the platform root reading scale to 18px, increased fixed-pixel landing/entry typography, labels and controls, and enlarged original booklet body text via its committed generator. Rebuilt Dashboard presentation, workspace navigation and pending-route layouts. Real health/model-info data, error handling, manual refresh, limitations and provenance remain; no new recognition features claimed.

Verification: strict type-check/build PASS (9.46s), existing API/status unit tests 16/16 PASS, frozen guard 1174/1174. Dashboard reviewed at 1440x900, 768x1024 and 390x844 with no tablet/mobile horizontal overflow; mobile navigation and pending-route handoff checked. Live Model ready and manual refresh checked. Hero flat resting state and settlement after pointer movement observed; healthy-sequence browser console had no errors/warnings. No new automated visual suite or GPU benchmark.

Screenshots outside Git: C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-workspace-redesign/ (dashboard-desktop.jpg, dashboard-tablet.jpg, dashboard-mobile.jpg, tiles-at-rest.jpg, tiles-after-movement.jpg). A full-page screenshot attempt timed out; viewport screenshots were captured successfully.

## Latest hover, alignment and actual-results correction

This supersedes the preceding 140ms inactivity interaction. Tiles no longer rotate; bevelled blocks remain on aligned grid axes, with a 2048px shadow map. Pointer hover produces raised relief, violet local colour and a subtle surface tint, which remain during stationary hover; pointer leave returns to neutral and flat. Rendering stops once settled. Removed the extra hero footer rule and aligned the Field Notes headings/rule.

Browser observed at the default desktop viewport: stationary hover depth/colour, neutral state after leave, straight resting seams and aligned Field Notes header. No console errors/warnings observed. Actual result pages and mobile layout were also verified; see RESULTS_HANDOVER.md for request IDs, screenshots and remaining limits. Production build and 29 tests pass. No GPU benchmark or automated visual/accessibility suite.

## Branded opening and PNG field report

The screenshot-requested opening captions, wordmark, Skip label, status/credit line and hero footer/movement captions have been removed. The new local entry uses an original generated hand photograph and a live Three.js C/check point-cloud mark. The hand is a still plate; the symbol has depth layers, rotation and pointer response. The Enter arrow has an accessible label and keyboard focus. No external scene iframe remains.

The shared brand now uses the transparent rendered logo. Manrope is self-hosted with its SIL OFL notice, shared by the landing and workspace. New workflow and research sections display actual saved API values. The booklet uses six distinct 1200 x 1600 PNGs generated from the same recorded inputs/results, plus a matching generated text transcript. All six PNGs were opened and inspected. Low-resolution input evidence is honestly magnified rather than redrawn.

Browser checks: default desktop and 390 x 844 mobile opening, hero, report and shared dashboard; 3D cover, pages 2-3 and 4-5, final-page state, next navigation, page PNG link, plain/3D switch and accessible transcript. Native page-turn controls and the workspace handoff were exercised. Mobile research-number overflow was corrected; final landing and dashboard document widths were 375px inside the 390px viewport (scrollbar consumes the remainder). No console errors/warnings observed. Temporary viewport override reset.

Production build and strict type-check pass; 29 existing tests pass, including unchanged capture hash/benchmark checks. All 1174 frozen files match. No new inference or research evaluation, GPU benchmark, reduced-motion emulation or automated accessibility audit.

Current screenshots outside Git: C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-brand-report/ (entry-desktop.jpg, entry-mobile.jpg, hero-desktop.jpg, hero-mobile.jpg, workflow-desktop.jpg, report-cover-desktop.jpg, report-spread-desktop.jpg, report-athn-decisions.jpg, report-mobile.jpg, evidence-mobile.jpg, dashboard-mobile.jpg).

Asset sources, full creative prompts, dimensions and regeneration command: ASSETS_AND_REPORT.md. Historical iframe/SVG descriptions above are superseded by this section.

## Animated-hand restoration and hero text backing

The preceding still-hand design is superseded. The opening now uses Cullen Webber's original rigged hand and volumetric-light implementation adapted locally, with the C/check replacing the floating glyph geometry inside the original ASCII material. Finger/wrist bones animate over time; no photographed hand or separate point overlay is used. Source hashes and pinned commit: src/light-study/UPSTREAM.json. Models and Draco decoders are local. The child scene is removed on Enter; replay creates a fresh isolated scene. Animation is capped at 30fps, skips hidden-page rendering and keeps the hand still under reduced-motion preference.

The reference requires Three.js 0.182.0 shadow comparison textures. The renderer and its types were aligned to that release; Vite's old optimized 0.181 cache was explicitly rebuilt. The original light beam, dust and hand shading were then observed alongside the new floating symbol, with no console errors/warnings. Two saved frames and pointer/camera response were inspected, and Enter/replay were exercised. Two regression tests use the real GLB skeleton metadata to verify that the actual hand/wrist rotations change over time. This checks pose updates; it is not a GPU-rendering test.

A 67% translucent, 16px backdrop-blurred layer now backs the hero copy. Tile seams are softened beneath the letters while tiles remain visible and interactive outside the panel. Desktop browser appearance and computed backdrop filter verified. Screenshots outside Git: C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-motion-fix/ (hand-frame-a.jpg, hand-frame-b.jpg, hero-glass-desktop.jpg). Responsive CSS remains, but the viewport override did not apply reliably in this check, so this entry does not claim a new mobile visual pass. No reduced-motion emulation or GPU benchmark.

31 tests pass, including the two new bone-motion regressions and existing capture-integrity checks. Frozen backend/research/data/model files remain unchanged.
