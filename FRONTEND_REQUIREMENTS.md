# Frontend requirements

Technical specification for the demo UI of ChequeVerify. The backend is frozen and complete (M9-A, M10-A). The frontend is not implemented in this repository yet.

Sources of truth, in order: `backend/app.py`, `backend/engine.py`, [openapi.json](openapi.json), [API_CONTRACT.md](API_CONTRACT.md), and the captured responses in `artifacts/M10/examples/`. If a field, endpoint or status code is not in those files, it does not exist and the frontend must not assume it. Where API_CONTRACT.md and the code differ, the code wins (see "Known differences" at the end).

The product is an academic prototype for human review. It is not certified bank software.

## 0. Recommended stack

| item | recommendation |
|---|---|
| language | TypeScript, strict mode |
| framework | React with Vite (Next.js is acceptable; no server-side features are needed) |
| styling | Tailwind CSS or CSS modules; no component library is required |
| tests | Vitest for unit tests, Playwright for end-to-end tests, axe or Lighthouse for accessibility |
| location | new top-level `frontend/` directory |

The collaborator may choose other tools if the requirements below still hold.

CORS: the backend allows `http://localhost:5173` and `http://127.0.0.1:5173` by default (Vite's dev port). For any other origin, start the backend with the environment variable `CV_CORS_ORIGINS` set to a comma-separated list of origins. Only GET and POST are allowed. Base URL for local use is `http://127.0.0.1:8000`; keep it in one configuration value.

## Endpoints used

| endpoint | used by | notes |
|---|---|---|
| `GET /health` | A | 200 `{"status":"ok","model_loaded":true}`; 503 `{"status":"model_unavailable","model_loaded":false}`. This body is not the standard error shape. |
| `GET /api/model-info` | A, B, F | `default_mode`, `modes`, `limitations`, `ready`, checkpoint hash, upstream commit, parameter count, decoding and preprocessing text |
| `POST /api/recognize` | C | form fields `image`, `field_type` (`numeric` or `written`), optional `mode` |
| `POST /api/verify` | B, C, D | two input forms (see section B); optional `mode` |
| `GET /api/benchmark` | E | `{"source": "...", ...contents of COMPARATIVE_METRICS.json}` |

Every response carries an `X-Request-ID` header, and JSON bodies carry the same `request_id` (the error body nests it under `error`).

## A. Dashboard

Purpose: say what the system is, whether it is ready, and where to go next.

- Call `GET /health` and `GET /api/model-info` on load. Show "model loaded" or "model not loaded" from `model_loaded` (health) and `ready` (model-info). If either request fails at network level, show "backend unreachable" and name the base URL.
- Show from model-info: `model`, `upstream_commit`, `checkpoint_sha256` (shortened with full value on request), `parameter_count`, `device`, `default_mode`, and the two modes with their descriptions. For `proposed`, show `modes.proposed.method`, `modes.proposed.config.id` and `modes.proposed.status` as returned.
- Show the `limitations` array verbatim, always visible on the dashboard.
- Navigation: Dashboard, Verify cheque (section B and C/D), Recognise one field, Research results (section E).
- When the model is not loaded, the submit controls on the other pages are disabled with an explanation (section F). The Research results page still works, because `/api/benchmark` reads a saved file.
- The dashboard must not display any number that is not returned by the API or bundled from a saved result file.

## B. Cheque verification workspace

Two input forms for `POST /api/verify`. The server accepts exactly one of them; any other combination returns 422 `invalid_input_combination`.

| form | fields sent |
|---|---|
| cheque image with boxes (main flow) | `cheque_image`, `numeric_roi`, `written_roi`, optional `mode` |
| two crops | `numeric_image`, `written_image`, optional `mode` |

Do not send the fields of both forms together. Do not send `numeric_roi` or `written_roi` in the two-crop form.

### B.1 Upload and preview

- Accept only PNG and JPEG. Check client-side as a convenience: file type, 8 MiB, 6000 px on the longest side, 24 million pixels, at least 8 px on each side. These are the backend defaults (`.env.example`) and can be changed by the operator, so the backend answer is authoritative and its error is shown if it disagrees.
- Show the image in a preview that fits the viewport. The image is never modified, re-encoded or resized before upload: send the original `File`. Re-encoding would change the pixels the model sees and could drop the EXIF orientation the ROI maths depends on.
- Keep the image only in memory (object URL). Revoke the object URL when the file is replaced or the page closes.

### B.2 Drawing, editing and resetting two boxes

- Two boxes: numeric amount and written amount. Distinct colour and label for each (colour must not be the only cue).
- Pointer events (mouse, touch, pen) to draw by dragging; `touch-action: none` on the drawing surface so touch drawing does not scroll the page. Boxes can be moved and resized after drawing.
- Keyboard-operable alternative: for each box, four numeric inputs (left, top, right, bottom) in natural image pixels, with the normalised values shown read-only beside them. Arrow keys on a focused box nudge it by 1 px (10 px with Shift). This is required, not optional (section F).
- Reset: one button per box and one for both.
- Submit is enabled only when both boxes exist, each passes the checks in B.3, a file is loaded, and no request is in flight.
- The server does not detect fields. The UI must say that the user marks the fields and must not offer "auto-detect".

### B.3 Coordinate conversion

Server rule (`parse_roi`, `crop` in `backend/app.py`): `numeric_roi` and `written_roi` are JSON strings of four numbers `[x0, y0, x1, y1]`, normalised to 0..1 against the uploaded image's width and height after EXIF orientation is applied, with `0 <= x0 < x1 <= 1` and `0 <= y0 < y1 <= 1`. The server rounds `v * width` and `v * height` to whole pixels; each cropped box must then be at least 8 px wide and 8 px high, otherwise 422 `roi_too_small`. Booleans and non-numbers give 422 `invalid_roi`.

Conversion, in three steps:

1. Pointer position to displayed-image coordinates. Take the pointer position relative to the displayed image's bounding rectangle (`getBoundingClientRect()` of the element that shows the image, after any CSS scaling or transform): `dx = clientX - rect.left`, `dy = clientY - rect.top`. Clamp to `[0, rect.width]` and `[0, rect.height]`.
2. Displayed to natural pixels: `sx = naturalWidth / rect.width`, `sy = naturalHeight / rect.height`; `px = dx * sx`, `py = dy * sy`. Use separate factors for x and y; do not assume the aspect ratio is preserved to the last pixel.
3. Natural pixels to normalised: `x = px / naturalWidth`, `y = py / naturalHeight`.

Steps 2 and 3 combine to `x = dx / rect.width`. Keep the stored box in natural pixels (or in normalised form) and derive the display rectangle from it, so a window resize never changes the submitted values.

After normalising, order the corners (`x0 = min`, `x1 = max`, same for y), clamp each value to `[0, 1]`, and reject the box in the UI if `(x1 - x0) * naturalWidth < 8` or `(y1 - y0) * naturalHeight < 8`. Use the same rounding as the server (round to nearest whole pixel) for this check. Send each ROI as `JSON.stringify([x0, y0, x1, y1])` with plain decimal numbers (up to 6 decimals is enough; the demo manifest uses 6).

Worked example. Natural image 1800 x 1200 px, shown at 600 x 400 CSS px (scale 3 in both directions). The user drags the numeric box from displayed (100, 50) to (300, 150).

| step | value |
|---|---|
| natural pixels | x 300 to 900, y 150 to 450 |
| normalised | x0 = 300 / 1800 = 0.166667, y0 = 150 / 1200 = 0.125, x1 = 900 / 1800 = 0.5, y1 = 450 / 1200 = 0.375 |
| form field | `numeric_roi=[0.166667, 0.125, 0.5, 0.375]` |
| server crop | pixels 300, 150, 900, 450 (600 x 300 px, above the 8 px minimum) |

The response's `rois.numeric_px` and `rois.written_px` give the pixel boxes the server cropped. In tests, compare them with the expected natural-pixel boxes (rounding can differ by 1 px from the 6-decimal values).

Edge cases:

| case | rule |
|---|---|
| EXIF orientation | The server applies `exif_transpose` before cropping, so ROIs refer to the rotated image. Use the rotated dimensions: `naturalWidth` and `naturalHeight` of an `<img>` element reflect EXIF orientation in current browsers. If drawing on a canvas, decode with `createImageBitmap(file)` (orientation applied by default) or verify the dimensions against an `<img>`; never combine canvas dimensions of the unrotated bitmap with a rotated preview. Test with an EXIF-rotated fixture. |
| CSS scaling | Always measure the rectangle of the element actually showing the image, at the time of the pointer event. CSS width, max-width, zoom containers and transforms all change `rect`. |
| `devicePixelRatio` | Irrelevant. Natural coordinates come from `naturalWidth`/`naturalHeight` and CSS-pixel rectangles; do not multiply by `devicePixelRatio`. |
| drag outside the image | Clamp to the image edge (step 1). |
| zero or reversed drag | Normalise corner order; reject if smaller than 8 px after scaling. |
| window resize or orientation change | Boxes are stored in natural or normalised form and redrawn; the submitted value does not change. |
| numeric inputs | Typed pixel values are clamped to `[0, naturalWidth]` and `[0, naturalHeight]`; left < right and top < bottom enforced before submit. |
| overlapping boxes | Allowed by the API. Show a non-blocking note. |

### B.4 Mode selector and submit

- Two options: `baseline` and `proposed` (ATHN). Initial selection is `default_mode` from `GET /api/model-info` (currently `proposed`). If model-info is unavailable, send no `mode` field and let the server choose, or select `baseline`; do not invent a default.
- Show next to the selector: baseline is the unmodified model and typically answers in well under a second per crop on CPU; proposed adds training-free text-height normalisation and can take tens of seconds on written-amount lines (measured 10 to 48 s typical for enlarged synthetic written lines; 5 of 89 test lines took more than 120 s, the longest 419 s; a full synthetic demo sheet took about 38 s in proposed mode). Source: HANDOVER.md and `artifacts/M8/`. Baseline is always selectable.
- Suggestion for live demos: default written-heavy demos to `baseline` for speed. This is a UI choice and does not change the backend default.
- Submit sends `multipart/form-data` via `FormData`. Do not set the `Content-Type` header manually (the browser adds the boundary).
- `/api/verify` runs two recognitions in sequence, numeric then written, each with its own timeout (section F).

## C. Recognition results

Data comes from `POST /api/verify` (`numeric` and `written` objects) and `POST /api/recognize` (one object). Fields that exist, and only these:

| field | type | display |
|---|---|---|
| `field_type` | `numeric` or `written` | label |
| `mode` | `baseline` or `proposed` | label |
| `raw_text` | string | verbatim, monospace, no trimming, no case change, no correction; show an explicit marker for an empty string |
| `parsed_value` | string like `"25000.00"` or `null` | show the string as returned; do not convert to a float. `null` is shown as "not parsed" |
| `parse_status` | `parsed` or `unparseable` | label |
| `beam_log_probability` | number | optional; if shown, label "model score (uncalibrated)". Never a percentage, never "confidence" |
| `preprocessing` | object | baseline: `method`, `applied`, `path`. Proposed: also `estimated_text_height`, `input_hw`, `scale`, `output_hw` when present. Show only keys that are present |
| `model_input_shape` | array | optional detail, e.g. `[1, 3, 122, 404]` |
| `latency_seconds` | object | `preprocess`, `queue_wait`, `inference`, `total` (all seconds). Show as numbers with units |
| `image` | `{width, height}` | `/api/recognize` only; the size of the image that was sent |
| `request_id` | string | `/api/recognize` top level; in `/api/verify` it is at the top level of the response, not inside `numeric` or `written` |

Verify responses additionally carry `rois` (`numeric_px` and `written_px`, each `[x0, y0, x1, y1]` in natural pixels; `null` in the two-crop form) and `total_latency_seconds` (sum of the two `total` values). The `numeric` and `written` objects of a verify response have no `image` field.

Layout: two cards side by side on wide screens, stacked on narrow ones. In ROI mode, show the cheque preview with the two boxes beside or above the cards and highlight `rois` as returned. Parsing is strict (see API_CONTRACT.md): no digit repair, no spelling correction. The UI must not offer to edit or auto-correct `raw_text`.

Currency markers: only `Rs`, `Rs.`, `PKR` or none are supported; anything else gives `unparseable` and therefore `review`. State this next to the results, using the `limitations` text from model-info.

Recognise-one-field page: one image, a `field_type` selector (`numeric` or `written`), a mode selector, then the object above.

## D. Verification decision

`decision` is one of three values, shown as a labelled badge (text plus an icon or shape, not colour alone):

| `decision` | badge text | meaning shown to the user |
|---|---|---|
| `accept` | "Amounts agree" | both values parsed and are equal. Neutral-positive styling, never a green tick that reads as approval |
| `flag` | "Amounts differ" | both values parsed and differ. Attention styling |
| `review` | "Needs human review" | at least one value could not be parsed. Neutral styling; this is a normal outcome, not an error |

- Show every string in `reasons` verbatim, in order. Reason strings start with a machine-readable prefix (`numeric_amount_unparseable`, `written_amount_unparseable`, `values_agree`, `values_disagree`). Show the full string; a friendlier label may be added beside it but must not replace it.
- Show `notice` verbatim, always visible below the badge. Not in a tooltip, not collapsed.
- Show `mode` and `total_latency_seconds`.
- Show the two parsed values side by side with `raw_text`, so a human can compare them with the image.
- Synthetic cheque fields: their written amounts never parse, so pairs built from synthetic written fields always end in `review`. When the demo uses such an image, the UI may state that `review` is the expected conservative outcome, but only in text attached to the labelled demo input, not as a general claim about results.

### Wording rules

| do not write | write instead |
|---|---|
| verified, genuine, authentic, valid cheque, approved, cleared (for `accept`) | "amounts agree" |
| confidence, accuracy, probability correct (for `beam_log_probability`) | "model score (uncalibrated)", or omit |
| error or failure (for `review`) | "needs human review" |
| fraud detected, tampering, forged, signature OK | not allowed anywhere |
| "AI-corrected", "fixed" (for any text) | not allowed; `raw_text` is shown as returned |

Include a persistent line: "Academic prototype for human review. Not certified bank software. A match is not proof of authenticity."

## E. Research benchmark dashboard

Source: `GET /api/benchmark`. Response is `{"source": "artifacts/M8/COMPARATIVE_METRICS.json", ...}` followed by the keys of that file: `split` (`test`), `datasets`, `pairs`, `improvements_vs_regressions`, `proposed_config`. The data is a saved locked-test result and is never recomputed. If the endpoint answers 404 `benchmark_unavailable`, show that message and nothing else on the page.

The frontend renders values as returned. It must not recompute, re-round differently, merge or reweight any metric. Display baseline and proposed side by side, with the `delta` where the file provides one.

### E.1 Datasets (`datasets`)

Each key is one dataset. Keys ending in `_SYNTHETIC` are synthetic; all other keys (`D1_gnhk_words_genuine`, `D4_cvl_numeric_genuine`, `D5_gnhk_numeric_genuine`, `D5_gnhk_words_genuine`) are genuine handwriting. Show two separate groups with distinct headings: "Genuine handwriting" and "Synthetic (font-rendered, not handwriting)". Never put them in one table or one chart without the group boundary.

Per dataset, show a row with:

| column | field |
|---|---|
| items | `n_eligible` (and `blank_fields` if shown) |
| CER | `cer.baseline`, `cer.proposed`, `cer.delta` |
| WER | `wer.baseline`, `wer.proposed`, `wer.delta` |
| exact match | `exact.baseline`, `exact.proposed` (counts) and `exact_rate.baseline`, `exact_rate.proposed`, `exact_rate.delta_pp` |
| value exact | `value_exact.baseline`, `value_exact.proposed`, `value_exact.n`, `value_exact.delta_pp`; present only for the numeric datasets and `D5_gnhk_words_genuine`. Show "not reported" when the key is absent |
| parseable | `value_exact.parseable.baseline`, `.proposed` when present |
| improvements and regressions | `improvements_vs_regressions[<dataset key>].exact_improvements` and `.exact_regressions` |

Other present fields (`relative_cer_reduction`, `coverage`, `failure_rate`, `punctuation`) may go in an expandable detail row. Lower CER and WER are better; say so in a caption. Null values (for example punctuation precision) are shown as "n/a".

### E.2 Pair decisions (`pairs`)

Four groups: `gnhk_pairs_genuine_constructed` (genuine), and `syn_all_SYNTHETIC`, `syn_natural_SYNTHETIC`, `syn_constructed_SYNTHETIC` (synthetic). Same separation rule as above. Each group has `baseline` and `proposed` objects. Per method, show:

| column | field |
|---|---|
| pairs | `n_eligible` |
| decisions | `decisions` (counts of `accept`, `flag`, `review`; a missing key means zero) |
| review rate | `review_rate` |
| decision coverage | `decision_coverage` |
| incorrect acceptance rate | `incorrect_acceptance_rate` |
| incorrect rejection rate | `incorrect_rejection_rate` (`null` shown as "n/a") |
| explicit mismatch detection | `explicit_mismatch_detection` |
| auto-accepted matches | `auto_accepted_matches` |
| confusion | `confusion`: keys of the form `match->accept`, `match->flag`, `match->review`, `mismatch->accept`, `mismatch->flag`, `mismatch->review`, shown as a 2 x 3 table |

Also present: `unresolved`, `flag_or_review_prf`, `decided_only`, `all_review`. These may be shown in a detail row. "Match" and "mismatch" refer to the ground-truth relation between the two amounts, as defined in `artifacts/M8/FINAL_EVALUATION_REPORT.md`; link or cite that report rather than redefining it.

### E.3 Required text on the page

- The data is the locked test split, produced once, and is a measurement of the frozen research method, not a product accuracy claim.
- Genuine pair results are on constructed pairs of genuine crops, not real cheques. No real handwritten cheques were available.
- Synthetic groups: with both methods every synthetic pair goes to review, because no synthetic written amount parses.
- `limitations` from `/api/model-info`, repeated here.
- Latency note (static text sourced from HANDOVER.md, not from the API): median per-crop latency 0.25 s baseline and 0.29 s proposed, with enlarged written lines often taking 10 to 48 s; 5 of 89 test lines took over 120 s, the slowest 419 s.
- The `proposed_config` returned (id `P1-A`, `band_lo`, `band_hi`, `target`, `min_scale`, `max_scale`) may be shown as the configuration used.

### E.4 Confidence intervals

`/api/benchmark` does not contain confidence intervals, and the API has no endpoint that serves them. They exist only in `artifacts/M8/STATISTICAL_ANALYSIS.json` (cluster bootstrap, keys under `results`: per dataset `cer_delta`, `cer_delta_ci95` as a two-element array, `exact_delta`, `exact_delta_ci95`, `exact_mcnemar`, plus `ALL_GENUINE` and `PAIRS_correct_automatic_decision`). The dashboard may show them only if the frontend bundles that file as a static asset, read-only and byte-identical to the repository copy (copy it at build time; never edit it), and labels it "static snapshot of STATISTICAL_ANALYSIS.json". Otherwise the dashboard omits CIs and says that intervals are in the report. Do not add a backend endpoint and do not compute intervals in the browser.

## F. UX requirements

### F.1 Layout and responsiveness

- Works from 360 px width upward. Single column below about 768 px; no horizontal page scroll. Tables scroll inside their own container on narrow screens.
- The drawing surface scales to the viewport; boxes remain operable on touch screens.
- Restrained, banking-style look: neutral palette, one accent colour, plain type, no decorative animation.

### F.2 Loading and duplicate submissions

- While a request is in flight: disable the submit button and the mode selector, show an indeterminate indicator and the elapsed time as a counter. No progress bar and no percentage, because the server reports no progress.
- Say what is running, for example "Recognising numeric then written amount"; do not claim which of the two is running, because the client cannot know.
- One in-flight request per action. Ignore a second click, Enter key or double submit until the first completes or fails.
- Cancel: an abort stops waiting in the browser only. Cancelling a browser request does not stop server computation, and the single inference slot stays occupied until the model call finishes. If offered, label it "Stop waiting" and warn that the server may stay busy.
- Client timeout: do not abort before 250 s (two recognitions at the 120 s default each), or use no client timeout. A shorter timeout would report failure while the server is still working.

### F.3 Validation and error display

Show `error.message` and `error.request_id` from any non-2xx JSON body of the form `{"error": {"code", "message", "request_id"}}`, and map `error.code` as follows. Wording below is guidance; keep `message` and `request_id` visible.

| status | `error.code` | cause | UI handling |
|---|---|---|---|
| 413 | `file_too_large` | file over `CV_MAX_UPLOAD_BYTES` (default 8 MiB) | ask for a smaller file |
| 413 | `image_too_large` | over 6000 px on a side or 24 M pixels (defaults) | ask for a smaller image |
| 415 | `unsupported_media_type` | content type not `image/png` or `image/jpeg` | ask for PNG or JPEG |
| 415 | `content_mismatch` | bytes do not match the declared type | ask for a valid PNG or JPEG file |
| 422 | `undecodable_image` | image cannot be decoded | ask for another file |
| 422 | `image_too_small` | under 8 px on a side | ask for a larger image |
| 422 | `invalid_roi` | ROI not a JSON list of four numbers in 0..1 with x0<x1, y0<y1 | highlight the offending box (message names `numeric_roi` or `written_roi`); redraw |
| 422 | `roi_too_small` | box under 8 px after scaling | highlight the box; enlarge it |
| 422 | `invalid_parameter` | `field_type` or `mode` not allowed (also raised if proposed mode is not configured) | show message; reselect |
| 422 | `invalid_input_combination` | field set matches neither verify form | programming error in the client; show message and the request id |
| 422 | `invalid_request` | required form field missing or invalid (message lists field names) | show message |
| 503 | `model_unavailable` | checkpoint not loaded | disable submits; show the model-not-loaded state; manual "Check again" |
| 503 | `busy` | no inference slot freed within `CV_QUEUE_TIMEOUT_S` (default 30 s) | honest busy message; manual retry button |
| 504 | `inference_timeout` | one recognition exceeded `CV_INFERENCE_TIMEOUT_S` (default 120 s) | timeout message (see F.4); manual retry; suggest baseline |
| 500 | `internal_error` | unexpected server error | generic message plus request id |
| 404 | `benchmark_unavailable` | `/api/benchmark` only: no saved results | show on the Research results page |

Other failures the table does not cover: a response that is not JSON, a network failure (backend unreachable or blocked by CORS), and a status code not listed. Show a generic message with the HTTP status and, if present, `X-Request-ID`. Do not invent a code. Note that FastAPI's own 404 for an unknown path has a different body (`detail`), so parse errors defensively. `/health` 503 uses the health body shape, not the error shape.

Client-side validation (file type, size, ROI size) runs before the request and uses the same wording, so the user sees the problem without a round trip.

### F.4 Busy and timeout behaviour

- 503 `busy`: "The server is processing another recognition. Try again in a moment." Retry is manual. No automatic retry loop, because a retry adds load to a single-slot CPU server.
- 504 `inference_timeout`: "Recognition took longer than the server limit. The server may still be working on it and may answer busy for a while." Offer a manual retry and a one-click switch to baseline. In `/api/verify`, a timeout in either recognition returns only the error; there is no partial result, so do not show the numeric result from a timed-out verify.
- After a 504, a following request can receive 503 `busy`. Explain this in the message; it is documented backend behaviour (the model call cannot be interrupted).
- The server cap on waiting for a slot never exceeds the inference timeout, so an abandoned request does not start model work later.

### F.5 Model-unavailable state

If `/health` returns 503, or any call returns 503 `model_unavailable`: disable submit controls on all recognition pages, state that the model is not loaded and recognition is unavailable, show a "Check again" button that calls `/health`, and keep the Research results page usable. Do not poll in a tight loop; check on page load and on the user's request.

### F.6 Baseline always available

Baseline is never disabled while the model is loaded. If model-info reports `default_mode` of `proposed` and the user hits a timeout, the retry offer defaults to baseline.

### F.7 Accessibility

- Every input, button and box has a programmatic label; the two boxes are named "Numeric amount box" and "Written amount box".
- Full keyboard operation: upload, numeric-input alternative for boxes (B.2), mode selector, submit, retry and navigation, with visible focus indicators and logical tab order. Drawing by pointer is never the only way.
- Contrast: at least 4.5:1 for text, 3:1 for UI components and box outlines (WCAG 2.1 AA). Decision and status are never conveyed by colour alone.
- Results and errors are announced: put the decision, error banner and status changes in an `aria-live` region (`polite` for results, `assertive` only for errors that block the user). Move focus to the result heading or error summary after a response.
- Respect `prefers-reduced-motion`. Images have meaningful alt text ("Uploaded cheque image, user-selected boxes shown as overlays").
- Run axe or Lighthouse accessibility on each page; no critical or serious axe violations.

### F.8 Privacy

- Do not store uploaded images (localStorage, sessionStorage, IndexedDB, Cache API, service worker) and do not send them anywhere except the backend.
- Do not log `raw_text`, `parsed_value`, images or image bytes to the console or to any analytics in production builds. No analytics or third-party scripts that see page content.
- The server also drops images after the response and logs only request id, path, status and latency.
- Demo inputs must be synthetic or consented. No real customer cheques. Show that rule next to the upload control.
- Labelled demo inputs (`data/demo/sheet_accept.png`, `sheet_flag.png`, `sheet_review.png` with their ROIs from `data/demo/demo_manifest.json`) are constructed composites of development-split crops, not cheques and not benchmark evidence. If the UI offers them as samples, label them that way. The manifest's `box_px` and `roi` values are the expected boxes, and the expected baseline decisions are accept, flag and review respectively.

## Out of scope

The frontend must not add, imply or mock any of the following; none exists in the backend:

- authentication, user accounts or roles
- banking transactions, clearing, deposit or payment actions
- signature recognition or verification
- fraud detection, forgery or tamper detection
- automatic field or amount-box detection
- text correction or editing of recognised values
- persistent storage of images or results (no history page)
- any endpoint, request field or response field not listed in this document
- recomputation of benchmark metrics or confidence intervals

## Points where the generated schema is incomplete

API_CONTRACT.md has been updated to match the code on `queue_wait` and on the verify sub-objects. One gap remains, in the generated schema only:
- openapi.json documents only 200 and 422 responses with FastAPI's default validation body. The real error body for 422 and all other errors is the `{"error": {...}}` shape in API_CONTRACT.md. Do not generate error types from openapi.json.
- `/health` (503) and the 404 for an unknown path do not use the `{"error": {...}}` shape. Parse defensively.
