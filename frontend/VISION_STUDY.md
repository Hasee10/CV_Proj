# Computer vision landing studies

Owner-directed replacement of the decorative hero sculpture and the two research metric cards. Changes are confined to frontend presentation and original vector/geometry illustrations; backend, preprocessing, data, weights and frozen measurements are untouched.

## The visual purpose

The hero now connects an actual input to actual readings. Its three controls expose:

- **Pixel relief:** an original Three.js intensity illustration of the stored 133 × 40 synthetic numeric DEV crop. Pixel darkness determines the height of instanced cells. This is an image visualization, explicitly not model attention, confidence or a learned feature map. The image is sampled at its full resolution here; a 160-column limit handles larger inputs. Original input bytes are never rewritten. Rotate by dragging or arrow keys; Home resets. The scene has no autonomous animation, stops rendering when settled/offscreen, caps DPR at 1.25, honours reduced motion, and falls back to the original image if WebGL is unavailable.
- **Original crop:** the byte-identical input image, shown without an invented enhancement or segmentation overlay.
- **ATHN scale:** a proportional SVG using saved model-input dimensions, 133 × 40 → 404 × 122; recorded scale 3.038; estimated text height 15.8 px; frozen target 48 px. It is labelled as a scale diagram rather than a processed-image preview.

The raw baseline `3003` / parsed `3003.00` and ATHN `3083` / parsed `3083.00` stay visible across views. The changed character is highlighted without rewriting either reading. The example is synthetic DEV evidence, not an accuracy claim. The primary action leads to the existing two-field verification workspace; a specimen link leads to recognition details.

The November 28 refinement removes the enclosing green card and nested viewport frame. A feathered pale wash lets the study share the hero surface while keeping the tile grid away from small labels. One crop branches through an SVG connector into the baseline and ATHN reading paths; input dimensions and the saved scale remain explicit. Controls use underlines, without another enclosing panel. Near-white pixels below 2% darkness stay flat in the relief to reduce cell-edge noise; all other cell heights retain the intensity mapping. This is display geometry only and never alters the stored image, API input, or preprocessing.

The unified hero was checked at 1920 × 1080, 768 × 1024 and 390 × 844 without page-width overflow. Relief rotation/reset, original crop and scale controls work, and no browser console errors were observed. All 52 tests, production build/type-check and the 1174-file guard pass. The pre-existing shared Three.js size warning remains. Updated previews are outside Git at `C:/Users/Administrator/.codex/visualizations/2026/11/28/chequeverify-unified-hero/`: `hero-desktop.jpg`, `hero-scale-desktop.jpg`, `hero-mobile.jpg`.

The research section is an interactive instrument rather than a pair of isolated headline numbers. All six frozen datasets remain selectable, with genuine/synthetic domains explicitly separated. Front-face column height encodes CER; equal-depth extrusion is decorative. Genuine plots share a labelled 0–50% axis and synthetic plots a labelled 0–110% axis. Original decimal CER values remain visible. Charts do not compare lengths across those different domain axes.

The CVL increase, exact-transcription versus exact-parsed-value distinction, 164/164 synthetic review decisions (146 eligible + 18 unresolved), 0/87 written synthetic parsed matches and overall genuine non-significance remain visible. No real handwritten cheques were evaluated. Raw JSON, complete metrics and historical latency limitations remain on the unchanged benchmark workspace.

## SVG artifacts

`public/study/athn-scale.svg` and six `public/study/cer-<dataset ID>.svg` files are standalone vector exports of the exact same React SVG components used in the UI. They include axis labels, direct values, accessible descriptions and a dark background. Export files use a system sans-serif fallback; the website uses self-hosted Manrope.

Rebuild from `frontend/`:

```powershell
npm run assets:study
```

The small Node wrapper uses Vite's bundled esbuild to render the existing TSX components with React's server renderer. It removes its temporary module after completion. It reads the nine stored responses selected by `public/results/latest.json` and makes no API requests. `public/study/provenance.json` records the capture run.

## Verification

- 52 frontend tests pass across six files, including study/data tests and verification deep-link checks for saved cases and invalid-query fallback.
- TypeScript and Vite production build pass. The existing shared Three.js chunk-size warning remains; the new relief module is lazy loaded.
- Browser checked at 1440 × 1000, 768 × 1024 and 390 × 844 CSS viewports. No page-width overflow. Original crop, scale and relief views, keyboard rotation/reset, six dataset selections, the CVL regression and synthetic >100% axis checked against their actual labels and values. No console errors observed.
- Lazy-reader placeholder space is reserved to prevent the research anchor shifting when the book loads.
- The original nine response/image hashes and exact benchmark equality remain covered by capture tests. All 1174 protected files match the frozen manifest.
- No inference, research evaluation, model training, custom upload or ROI-editing changes were performed.

Screenshots are outside Git at `C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-vision-study/`: `hero-desktop.jpg`, `hero-scale-desktop.jpg`, `research-desktop.jpg`, `research-synthetic-desktop.jpg`, `hero-mobile.jpg`, `specimen-mobile.jpg`, `research-mobile.jpg`, `hero-tablet.jpg`.

## Workflow trace and compact research revision

The workflow now follows a complete stored two-field verification response through three connected stages: original numeric/written ROI crops, untouched raw readings and parsed values, then the recorded decision. Agreement, mismatch and human-review buttons switch among `sheet_accept`, `sheet_flag` and `sheet_review`. Original source images are clipped in SVG using the server's pixel coordinates and the image's natural dimensions. Both source and reading rows align at 116px on desktop. Request IDs and original JSON remain linked; genuine handwriting, synthetic input and constructed DEV status remain explicit. Review keeps raw `mummisessing` and a null parsed value rather than fabricating a number.

“Inspect this comparison” links to `/verify?example=<saved ID>`. The existing verification screen selects that record on entry and safely falls back to its normal first case for unknown IDs. Manual model requests and their safeguards are unchanged; selecting a landing example makes no inference request. The review handoff was checked in the browser with Review example selected in the workspace.

Research chart height no longer expands with the surrounding column. Native SVG geometry uses a compact 640 × 250 composition, direct values remain labelled, dataset navigation and counters have less excess padding, and the CER definition is a keyboard-accessible disclosure. All six datasets, raw values, denominators and the visible scientific limitations remain available. At the same 1920 × 1080 CSS viewport, the section measures approximately **936px rather than 1340px**, a **30% height reduction**. Workflow height is approximately 882px rather than 1001px at that width. No content is clipped by a fixed section height.

Desktop, 768 × 1024 tablet and 390 × 844 mobile were checked without page-width overflow, including the long unparseable reading. Comparison controls, correct ROI coordinates, the matching workspace link, synthetic CER above 100%, and the CER disclosure were inspected. Build/type-check and all 52 tests pass; all 1174 protected file hashes match. The seven SVGs were rebuilt from the same components. Existing Three.js bundle-size warning only.

Additional screenshots: `C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-workflow-compact/` — `workflow-desktop.jpg`, `research-desktop.jpg`, `workflow-mobile.jpg`, `research-mobile.jpg`, `workflow-tablet.jpg`.

## November 28 compact report and artwork refinement

The field report keeps its original automatic spread layout, nine page PNGs and page-turn controls. The reader height now follows the viewport; duplicate accessible-text toggles, text-version disclosure and PNG/SVG export links were removed from the visible UI. Report text remains available to screen readers and appears as a fallback if the reader errors. At 1920 × 900, the whole section measures about 755px and its bottom sits at 864px after anchor navigation. At 1440 × 800, it measures about 647px and ends at 755px. Both include the floating-header offset and controls.

Hero copy now contains a concise project label, headline, one explanation and two actions. The redundant method list and fine print have been removed. Pixel relief has taller intensity-based extrusion, separated face materials and an adjusted camera for visible sidewalls at rest. The source image and recognition pipeline remain unchanged; there is no autonomous relief rotation.

Only the workflow's comparison illustration changed: two generated transparent PNG assets replace its flat node shapes. Live parsed values and outcome symbols are still SVG text taken from the selected saved response. CSS animates the nodes and connectors, with a reduced-motion still state. Other workflow content, crop rendering, decisions and links are unchanged. Exact prompts, dimensions and provenance are in `public/workflow/ARTWORK.md`.

All 52 tests, production build/type-check and the frozen-file guard pass. Existing shared Three.js size warning only. Checked report page turning, all three workflow outcomes, animated-node styles, relief keyboard rotation/reset, and 390px mobile without width overflow. No console errors observed. Updated previews: `C:/Users/Administrator/.codex/visualizations/2026/11/28/chequeverify-final-refinement/`.

## Explicit spreads and research spiral

The latest reader revision explicitly selects spread layout at widths of 768px and above, starts desktop on pages 2–3, and uses single-page layout below that breakpoint. The cover remains reachable through Previous. Desktop reader height is now 560px at 1920 × 900; section bottom is approximately 850px after anchor navigation. At 1440 × 800 the reader is 460px and section bottom is approximately 749px. Mobile framing compensates for LeafThrough's reserved turning space in both dimensions, inside a clipped reader stage, so the visible page fills the available width. Counters are normalized when crossing layout breakpoints. Page turning was checked in both modes.

`ResearchSpiral.tsx` adapts the rolling vertical-panel motion found in Synordinate's local `dist/progress-scene.js` and `dist/progress-motion.js` into a coiled dataset navigator. It is original Three.js geometry for this application: two thin paths, bevelled rolling slats, six selectable paired rungs and travelling points. The sculpture does not encode CER; that is explicit in its caption and accessible description. Live measured CER, exact-match counts and denominators remain beside it, with all six datasets selectable. The regression, synthetic 164/164 review count, 0/87 written exact parses, overall genuine non-significance and absence of real-cheque evaluation remain visible. Complete evidence stays linked in the benchmarks workspace. The former SVG columns are retained as standalone exports and are no longer the landing illustration.

Spiral rendering is capped at approximately 30fps and DPR 1.25, stops offscreen or in a hidden tab, respects reduced motion and provides a Pause control and fallback. Horizontal dragging orbits, paired-node hover/tap selects a dataset, arrow keys traverse datasets, and Home resets the orbit. GPU resources and listeners are disposed on unmount. Six dataset readouts, synthetic CER above 100%, pause, keyboard selection, desktop/mobile layouts and page-width overflow were browser checked. No console errors observed. Screenshots: `C:/Users/Administrator/.codex/visualizations/2026/11/28/chequeverify-spiral-reader/`.

## Evidence depth gallery, wavy cubes, glass xylophone and visual calibration

The hand opening is superseded by a native-scroll depth gallery inspired by the owner-provided Codrops DepthGallery reference. Three 1200 × 1500 PNG plates contain actual saved project evidence: the genuine constructed `1` / `one` fields; the same synthetic numeric crop with baseline `3003` and ATHN `3083`; and the unparseable synthetic written response `mummisessing`, retained as null and human review. Abstract generated material images were rejected and are not used or copied into the project. The evidence plates are deterministic editorial composites, not AI-generated handwriting or new inference. Their combined PNG size is 396,784 bytes. Source provenance is in `public/gallery/provenance.json`; regeneration uses `.venv/Scripts/python.exe frontend/scripts/create-gallery-evidence.py` from the repository root.

CSS perspective, opacity and blur place the plates at different depths. Native scrolling advances through them and the existing site emerges below the sticky stage. Chapter controls, immediate skip, replay, deep links and reduced-motion crossfades remain available. The opening does not create an iframe or load the archived hand GLB scene. Its first frame resets correctly rather than restoring an intermediate gallery position.

The hero grid now has near-contiguous regular cells, a more frontal camera, a local depth/tilt field and iridescent lavender response based on Wavy Cubes. It remains flat when the pointer leaves and retains the translucent copy surfaces. The earlier slat-and-wire spiral is replaced by rounded, physically shaded glass capsule bars, based on the owner's Codrops Xylophone reference. Sixty-four instanced bars use a local generated studio environment, physical transmission and thin-film iridescence; there are no copied shaders or reference assets. Six bands navigate the actual saved datasets. The scene includes pause, drag, keyboard selection, reduced motion, offscreen/background suspension and disposal; geometry remains illustrative.

`visual-system.css` supplies the shared ivory/graphite/amber/violet palette and a 16px base scale, with calibrated body text, captions, headings and numeric readouts. It also covers the workspace, preserving semantic status colors. Explicit contrast corrections keep the welcome card readable; narrow layouts stack research and result columns. All four workspace routes, 1280px desktop and 390px mobile were checked, including gallery handover, no horizontal overflow, synthetic CER above 100%, the CVL regression, and scene controls. No browser console errors were observed. All 54 tests and production build/type-check pass; all 1174 frozen hashes match. Existing shared Three.js bundle-size warning remains. Previews: `C:/Users/Administrator/.codex/visualizations/2026/11/28/chequeverify-depth-glass/`.


### 28 November 2026 - additional DEV samples and simplified opening

Six evidence panels now enter from both sides (three from the left). Only the small Scroll control remains around the gallery. The fixed opening dissolves over the hero and releases the site at scroll zero, removing the stacked section boundary.

Three predetermined DEV crops were captured sequentially in both modes: CVL_135579_0002_10, GNHKP_eng_EU_310_w016, SYN_0013_num. Actual baseline/ATHN outputs: 135529/135529, a/7, ting/1737. Failed parses stay null. No TEST inference or outcome filtering. Exact bytes, hashes and request IDs are under public/results/20261128T054632Z-gallery and public/gallery/samples.json. Original captures/latest index are untouched. The hero selects among all three. Its relief uses display-only paper-relative darkness; source images and model inputs remain unchanged.

Removed the spiral pause control, legend and visible drag/geometry captions. Six dataset selections now produce different glass tints and an amber selected band. The Genuine handwriting / Synthetic fields toggle filters the dataset controls and synchronizes with sculpture selections. Scientific limitations remain visible; geometry stays illustrative in its accessible description.

The reader defaults closed at 1/9. Desktop opens to 2-3/9; mobile opens to 2/9. Browser checks at 1280x900 and 390x844 covered opening handover/replay, sample changes, source toggle/color response and reader behavior. No horizontal overflow or browser errors observed. Verification: 57 tests across eight files passed, production build/TypeScript passed, all 1174 frozen files matched. Existing shared Three.js chunk size warning remains.


### 28 November 2026 - live observation desk and interactive evidence

- Dashboard now separates current-tab operational KPIs (completed live API requests, parsed fields/total fields, verification reviews and measured mean backend total time) from frozen research. Empty states start at zero, without fabricated activity. Session response metadata survives reload in sessionStorage, with JSON export and clear controls; uploaded images are not stored. Sample cards link directly to the appropriate live input.
- Live recognition defaults to the new lab: seven distinct DEV examples, PNG/JPEG field uploads, numeric/written selection, baseline/ATHN/paired mode, explicit run, elapsed timer, stop-waiting control, unchanged raw readings, strict parsed values and downloadable response JSON. Paired calls run sequentially. Live verification supports the three original ROI demos and two uploaded field crops. Archived comparisons remain available, including the original workflow deep links.
- Captured four predetermined extra DEV inputs in both modes, with no outcome filtering: CVL_136075_0002_03, SYN_0031_num, SYN_0032_num, SYN_0013_words. Exact API bytes and source hashes are under public/results/20261128T055842Z-workspace; generated/workspaceSamples.ts holds their recorded display values. Actual readings: 136075/136075, Ban/8312, coon/6815, comansinsuratimen/onesesererestiondndnderensiven. Written parses remain null. Only DEV inference; no research rerun or frozen changes.
- Benchmarks now have interactive paired bars (CER, WER, exact transcription rate), source filters, dataset inspection with percentage-point changes, a decision donut and an outcome heatmap. Both decision charts share cohort/method controls. Donut includes unresolved decisions; the confusion heatmap excludes them, with explicit denominators. Bar widths use actual values, including true zero. Raw tables and unchanged source JSON remain below. No dataset aggregation misrepresents the research.
- Desktop navigation collapses to an icon rail, retaining readable labels/tooltips and a persisted preference. Pip is an original SVG field-guide character with local contextual help, suggestions and keyboard dismissal, available in the sidebar or bottom-left on mobile. It is explicitly local help; the user deferred Groq integration to the end. No API key or external chat request is used.
- Replaced the opening publication PNGs with six native specimen frames: six distinct inputs, original crops, actual decoder readings/model input dimensions and our logo. Frames enter from both sides and dissolve into the hero. The research leaflet remains a separate nine-page publication, closed by default. Per-scroll blur filters were removed; no idle JavaScript animation loop is used for the opening. Reduced-motion uses a single active specimen. The enlarged spiral uses six distinct tinted bands that shift palette on selection, with no pause control.
- Browser verification: 1280x900 and 390x844. Tested actual paired recognition for 8312; an uploaded 6815 field; live demo mismatch; verification with uploaded numeric and written DEV crops, returning human review; KPI updates to 6 requests, 5/8 parsed fields, 1 review and 2.63 s mean backend time; session persistence after reload; navigation collapse/expand; local guide answer; chart filtering and synthetic 164-decision donut versus 146 eligible/18 unresolved matrix; closed leaflet; branded opening and mobile handover; enlarged multicolor spiral. No horizontal overflow or console errors observed. These QA session statistics are local measured examples, not research metrics.
- Validation: 64 tests across nine files; production TypeScript/build passed; existing shared Three.js chunk-size warning remains. All 1174 frozen files match the guard. No backend, model, dataset or research metric modifications.
