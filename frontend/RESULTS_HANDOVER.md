# Actual backend results — 27 November 2026

The backend and Vite preview were started using the existing environment. Nine HTTP 200 responses were captured in `public/results/20261127T081154Z-cbb492/`; `public/results/latest.json` selects this complete run. Original JSON response bytes, byte-identical DEV input copies, SHA-256 hashes, request fields, request IDs, timestamps, checkpoint hash and source commit are recorded in its manifest. This is a demonstration capture, not a new accuracy evaluation.

## Captured results

| Request | Actual outcome |
|---|---|
| GET /health | Model loaded |
| GET /api/model-info | Frozen checkpoint and configuration |
| GET /api/benchmark | Existing M8 metrics; no evaluation rerun |
| POST /api/verify, agreement DEV sheet | accept; numeric `1`, written `one`, both parsed `1.00` |
| POST /api/verify, mismatch DEV sheet | flag |
| POST /api/verify, review DEV sheet | review; written text unparseable |
| POST /api/recognize, synthetic numeric baseline | raw `3003`, parsed `3003.00` |
| POST /api/recognize, identical synthetic numeric ATHN | raw `3083`, parsed `3083.00` |
| POST /api/recognize, genuine word baseline | raw `one`, parsed `1.00` |

Both numeric methods use the same input. This single DEV example does not establish accuracy. Genuine handwriting and synthetic inputs are labelled separately. The three sheets are constructed demonstrations, not real bank cheques.

## Application behaviour

- `/dashboard`: live readiness and capture availability.
- `/verify`: three captured decisions, original images and returned pixel ROIs, raw text, decimal-string/null values, reasons, notice, request ID and timings.
- `/recognize`: three captured field results, including baseline and ATHN on the same crop; preprocessing, model shape and uncalibrated beam score in details.
- `/benchmarks`: exact frozen API metrics, genuine/synthetic groups, pair decisions and confusion details. Eligible and unresolved pair counts retain their original denominators; all 164 synthetic decisions are review, of which 146 have eligible labels.
- Fixed-example reruns are explicit button actions. They use the original input bytes and captured ROI/mode fields. A fresh response is held only in memory and clearly labelled; Saved JSON continues to download the original disk capture. Duplicate submissions are blocked, errors retain saved results, and leaving the page aborts browser waiting. Server work can continue after abort. No automatic retries.

Custom image upload, interactive ROI editing, the full F2–F6 acceptance workflow and a complete application integration suite remain unfinished. M9-B and M10-B remain PARTIAL.

## Reproduce the stored run

From the repository root, with the existing loaded-model backend at `http://127.0.0.1:8000`:

```powershell
.\.venv\Scripts\python.exe -X utf8 frontend/scripts/capture_backend_results.py
```

Each successful run creates a new UTC folder. Older captures are not overwritten. The latest index changes only after the entire run succeeds. Inference uses only the selected DEV examples; the benchmark request only reads the saved locked-test file. No locked-test inference, training, parameter changes or frozen-file edits.

## Verification

- Production build and strict type-check pass; 29 tests pass across API handling, byte/hash preservation, input identity, saved benchmark equality and page loading/rendering. Loading-state regression is covered.
- Browser: all three saved decisions selected successfully. Fresh agreement rerun returned request `8f6812aefb94`, accept, `1` / `one`, total 1.6631 s. Fresh numeric ATHN returned request `ffc39382e8a1`, `3083.00`, total 1.3509 s. These timings are individual observations.
- Benchmark manual refresh reached the live API and retained saved-file provenance.
- Verification and benchmark pages checked at 390×844 with no page-width overflow; tables scroll within their regions. Desktop results reviewed at the default browser viewport (1129×837).
- Hero stationary hover retains violet colour and raised relief; leaving returns it to a neutral flat surface. Tile rotation removed, header rules aligned, overlapping hero footer rule removed. No console errors or warnings observed during this check. No GPU benchmark or automated accessibility audit.

Screenshots outside Git: `C:/Users/Administrator/.codex/visualizations/2026/11/27/chequeverify-live-results/` (`verification.jpg`, `verification-mobile.jpg`, `benchmarks-mobile.jpg`, `hero-rest.jpg`, `hero-hover.jpg`).
