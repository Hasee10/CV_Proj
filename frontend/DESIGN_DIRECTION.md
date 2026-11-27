# Visual integration correction - 27 November 2026

This supersedes the placement decisions in the first F1 delivery. All three selected experiences now have an implemented place.

1. Entry: original Cullen Webber hosted volumetric-light demonstration, full viewport, with visible credit and immediate Enter/Skip. Cross-origin iframe, no-referrer, scripts/same-origin only, no camera, microphone or application data access. Removed entirely on entering the landing. Not loaded when reduced-motion is requested. Requires internet; source/model redistribution rights were not declared by the reference repository, so they were not copied.
2. Landing hero: local Wavy Cubes-inspired tiled surface following https://projects.arkon.digital/threejs/wavy-cubes/. Edge-to-edge pale cube tiles, fine seams, depth waves and a lavender pointer highlight replace the spherical cluster. One instanced mesh; capped at 30fps and DPR 1.25, pauses hidden/offscreen, supports reduced motion. Decorative, not model output.
3. Field Notes section: actual LeafThrough 0.1.8 React integration. Six original local SVG pages, curved paper and page turning, Previous/Next, keyboard support, plain mode and a complete text transcript. Content explains purpose, manual fields, LoGo-HTR, ATHN, decisions and limitations; no fabricated metrics. This is an explanatory companion, not a replacement for the future benchmark page.

Palette: pale tiled hero, deep green text and lavender interaction; paper #e6e8df and deep green #132b28 continue in the field notes and closing section. The application dashboard retains its F1 palette and live API integration.

Runtime: first Entry only; then Wave Grid; LeafThrough loads as the field-notes section approaches the viewport. No new backend endpoints or changes to research or data. Verification/recognition/benchmark routes remain pending their existing milestones.

Credits: public/visual-credits.txt and public/leafthrough-license.txt. Booklet artwork source: scripts/create-fieldnotes.py.
