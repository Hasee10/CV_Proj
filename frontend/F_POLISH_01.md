# F-POLISH-01 — visual refinement verification

Implemented 27 November 2026. The supplied HTML was inspected as design guidance; the existing React application, routes and typed client remain the implementation. Workspace styling is scoped under `.app-shell`. The owner's subsequent landing request also adds the right-hand cluster and refines the hero, workflow, research, closing, header and footer.

## Delivered

- Dashboard: compact live readiness, verification entry, labelled explanatory cheque-field SVG, real engine identity, three route cards and actual historical highlights.
- Verification: evidence/result columns, bounded original image, server-returned regions in the same SVG coordinate space as the image, magnified figures/words views, teal/violet field identity, exact reasons, values, raw text and latency. Disclosure panels retain original JSON and request metadata.
- Recognition: byte-identical saved input compared across baseline and ATHN, with separate source labels, raw readings, decimal values, preprocessing/inference/total times and an explanatory pipeline. Written examples remain a single result rather than inventing a counterpart.
- Benchmarks: grouped CER bars on a shared 0–110% scale, exact-value counts, decision stacks with eligible/unresolved counts, visible limitations, and collapsed original tables, confusion matrices and configuration.
- Landing: a feathered translucent veil replaces the bordered hero card. An original interactive cubic sculpture references Francesco Michelini's Codrops 3DCluster; drag/arrow keys rotate it and hover separates its parts. It is explicitly decorative. Tiled relief remains cursor-driven. The opening hand renderer and assets are unchanged.
- Report: nine 1200 × 1600 PNG pages, preserving original quantitative pages and adding review failure, genuine/synthetic domains, and system context. Three SVG companions, accessible text and direct image links accompany the reader. Generated artwork is marked as conceptual.

## Data and requests

All nine original response files and input images in `public/results/20261127T081154Z-cbb492/` remain byte-identical. Integrity tests check response hashes, source-image hashes, unchanged source bytes and exact equality with `artifacts/M8/COMPARATIVE_METRICS.json`.

Same-input numeric baseline remains raw `3003`, parsed `3003.00`; ATHN remains raw `3083`, parsed `3083.00`. Saved preprocessing time is `0.0513` seconds. Review keeps written raw `mummisessing` and null parsed value. Synthetic counts remain 146 eligible + 18 unresolved = 164 review decisions. Genuine automatic decisions remain 24 → 27 / 52. Synthetic exact values remain 0 → 17 / 77 and written 0 → 0 / 87. Raw numeric metrics are preserved; chart percentages are presentation formatting only.

One manual baseline agreement rerun was performed through the UI: request `58e07f9050a6`, figures `1`, words `one`, both parsed `1.00`, decision `accept`, total `0.9885` seconds. This response was labelled fresh and held in memory; original captures were not overwritten. Saved mismatch and review selections were inspected. Benchmark refresh read the frozen metrics via the API and displayed “Live API · saved metrics file”; no evaluation or training was run.

## Verification

- Frontend tests: 38 passed across five files, including seven new presentation/data-mapping tests and two original hand-skeleton motion regressions.
- TypeScript and production Vite build: pass. Vite retains the existing shared Three.js chunk-size warning; visuals are lazy loaded and workspace routes introduce no WebGL.
- Frozen-file guard: all 1174 files match.
- Browser: all four workspace routes checked at actual measured 1440 × 900, 768 × 1024 and 390 × 844 CSS viewports; no page-width overflow. Expanded raw tables also fit through contained scrolling on mobile. Keyboard menu opening and route activation, cluster arrow-key rotation, report Next controls through pages 8–9, and direct PNG/SVG links checked. No browser error/warning logs observed during workspace checks.
- Original 900 × 262 verification sheet and 133 × 40 recognition input inspected. ROI overlay and underlying image share a viewBox, so letterboxing applies to both equally. Actual agreement numeric rectangle is x845/y40/w15/h26; written is x40/y106/w231/h76. Crops use those exact source coordinates.
- Landing desktop/mobile, workflow, research cards, closing/footer and new booklet art visually inspected. Temporary viewport override reset.

## Screenshots

Directory: `C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-workspace-polish/`

| Page | Desktop | Tablet | Mobile |
| --- | --- | --- | --- |
| Dashboard | `dashboard-desktop.jpg` | `dashboard-tablet.jpg` | `dashboard-mobile.jpg` |
| Verification | `verify-desktop.jpg` | `verify-tablet.jpg` | `verify-mobile.jpg` |
| Recognition | `recognize-desktop.jpg` | `recognize-tablet.jpg` | `recognize-mobile.jpg` |
| Benchmarks | `benchmarks-desktop.jpg` | `benchmarks-tablet.jpg` | `benchmarks-mobile.jpg` |

Additional captures: `landing-desktop.jpg`, `landing-mobile.jpg`, `landing-workflow.jpg`, `landing-evidence.jpg`, `landing-closing-footer.jpg`, `book-new-review-page.jpg`, `book-new-pages.jpg`. Screenshots stay outside the repository.

## Remaining scope

M9-B and M10-B remain PARTIAL. The UI inspects and reruns recorded DEV examples. Custom file upload and interactive ROI selection/editing are not implemented or claimed complete. Abort, duplicate-request protection, structured error handling and saved-result offline availability retain their existing client logic; current browser checks exercise the normal connected path. No new automated accessibility audit or complete backend/research test run was performed.
