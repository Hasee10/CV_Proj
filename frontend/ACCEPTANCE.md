# F1 acceptance - 27 November 2026

Status: VERIFIED for F1 foundation only. M9-B overall remains PARTIAL; M10-B full recognition integration remains NOT STARTED.

## Implemented

- Procedural Three.js light/document introduction, original code and generated texture; lazy loaded separately from the application.
- React/strict TypeScript/Vite/Tailwind/Lucide/React Router shell; desktop sidebar, mobile navigation, route titles, skip links and focus handling.
- Dashboard uses real GET /health and GET /api/model-info. Model fields, modes, default, limitations and expandable checkpoint/pipeline details come from API responses.
- Manual refresh, loading, model-ready, model-unavailable, offline and unexpected-response handling. Valid /health 503 handled separately from errors.
- Verify, recognize and benchmark routes explicitly pending F2/F3/F4. No inference request triggered.
- Selected effect placements and palette recorded in DESIGN_DIRECTION.md. Leafthrough and cubes are not implemented in F1.

## Commands and results

From frontend/:
- npm install --no-audit --no-fund: succeeded after replacing an unavailable latest dependency chain with pinned releases; lockfile included.
- npm run build: PASS, includes tsc --noEmit. Final Vite build 10.99 s. Main JS 250.59 kB (79.85 kB gzip); lazy 3D JS 491.65 kB (127.73 kB gzip); CSS 16.81 kB (4.78 kB gzip).
- npm test: PASS, 16/16 tests in one file, one worker. Covers actual saved model-info, valid health 503, inconsistent health body, structured errors, non-JSON errors, unknown JSON errors, malformed success, network failure, cancellation and readiness states.
- npm audit --omit=dev --audit-level=high: 0 vulnerabilities, after updating React Router to 7.18.7. This was a production dependency audit, not a full tooling audit.

From repository root:
- .venv/Scripts/python.exe scripts/guard.py --verify: all 1174 frozen files match.
- git diff --check: PASS before staging; final staged review required before commit.

## Live verification

- Backend started using existing venv on 127.0.0.1:8000; GET /health returned model_loaded true.
- Browser dashboard showed LoGo-HTR, 6,385,537 parameters, cpu, proposed default, ATHN P1-A and backend limitations.
- Stopped only the server started for this task; browser showed Backend unreachable.
- Started create_app(load_model=False) temporarily on the same port without editing backend files; /health 503 and model-info ready false produced Model not loaded.
- Stopped that temporary server and restored normal real-model server; /health returned model_loaded true again.
- No recognition, research experiments or expensive inference tests run.

## Browser review

- Inspected introduction/dashboard at 1440 x 900, 768 x 1024 and 390 x 844. Fixed route-focus scrolling and mobile paper/caption overlap discovered during review.
- Checked mobile open/close navigation and all pending routes. Enter activated workspace/navigation; Escape closed the menu and returned focus to its toggle.
- Mobile/tablet document widths did not exceed viewport widths. Backend limitations remain in the page, not behind a disclosure.
- No unexpected console errors/warnings during initial healthy dashboard and route review. Deliberate offline/unavailable checks subsequently produced expected browser network/503 entries.
- Accessibility review was manual: semantics, accessible control names, keyboard navigation and status announcements. No axe/Lighthouse audit or automated full browser suite was run in F1.
- Reduced-motion and no-WebGL fallback paths implemented but not separately browser-emulated. No measured GPU frame-time or low-end hardware benchmark; subjective motion review remains appropriate.

Screenshots (outside Git): C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-f1/
- opening-desktop.jpg, opening-tablet.jpg, opening-mobile.jpg
- dashboard-desktop.jpg, dashboard-tablet.jpg, dashboard-mobile.jpg
- dashboard-offline.jpg, dashboard-model-unavailable.jpg

## API observations

The code wins over documentation: health/model-info/benchmark successful bodies do not all include request_id despite a broad statement in FRONTEND_REQUIREMENTS. The frozen CORS middleware does not expose X-Request-ID to cross-origin browser JavaScript. Use structured error-body IDs; header fallback is best-effort. No backend change made.

## Scope / startup

Changes limited to frontend/ and an appended status entry in PROJECT_TRACKER.md. Dependencies listed exactly in package.json and package-lock.json. No source/assets copied from the visual references.

Frontend command from root: npm --prefix frontend run dev
URL: http://127.0.0.1:5173/
Backend command from root: .venv/Scripts/python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

Commit/push result is reported separately after final diff review; this document does not claim a future push succeeded.
