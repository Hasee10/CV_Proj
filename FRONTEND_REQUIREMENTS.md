# Frontend requirements (for the collaborator building the demo UI)

The backend is complete (M9-A). The frontend is **not** implemented in this repository. This file says what it must do. The data shapes are in [API_CONTRACT.md](API_CONTRACT.md) and [openapi.json](openapi.json).

## Screens

### 1. Verify a cheque (main demo flow)
1. The user uploads a PNG or JPEG cheque image.
2. The user draws two rectangles on it: one around the numeric amount, one around the written amount. Convert each box to normalised `[x0, y0, x1, y1]`, measured against the image's natural pixel size, not the on-screen size.
   - Apply EXIF rotation before drawing, so the boxes refer to the same orientation the server uses. Browsers rotate `<img>` elements automatically; a canvas may not.
3. A mode switch offers `baseline` and `proposed`. Default it to `default_mode` from `GET /api/model-info`.
4. Submit `POST /api/verify` with `cheque_image`, `numeric_roi`, `written_roi` and `mode`.
5. Show:
   - the decision as a badge: accept green, flag red, review grey;
   - every string in `reasons`;
   - both `raw_text` values verbatim, and the parsed values;
   - per-field latency and `total_latency_seconds`;
   - the `notice` text. It must stay visible, not hidden in a tooltip.

### 2. Verify two crops
The same flow without boxes: two file inputs, `numeric_image` and `written_image`.

### 3. Recognise one field
Upload one crop, choose `numeric` or `written`, call `POST /api/recognize`, and show `raw_text`, `parsed_value` and `parse_status`. In proposed mode, also show `preprocessing.estimated_text_height` and `preprocessing.scale`.

### 4. Results page
Render `GET /api/benchmark` as tables of baseline against proposed. Show it as returned: do not round differently or recompute anything. Label the synthetic datasets as synthetic.

### 5. Status
Poll `GET /health` on load. If it returns 503, disable the submit buttons and say the model is not loaded.

## Wording rules (these come from the project's honesty constraints)
- Do not call `beam_log_probability` a confidence, accuracy or probability of being correct. Leave it out of the UI or label it "model score (uncalibrated)".
- Never show "verified", "genuine" or "authentic" for `accept`. Use "amounts agree".
- `review` means "needs a human". It is not an error state.
- Say that the app is an academic prototype and not bank software.
- Do not offer to auto-correct recognised text.

## Errors
Show `error.message` and `error.request_id` from any non-2xx response. Treat 503 `busy` and 504 as retryable. Requests can take a while: about 0.3 s for a short crop, but up to tens of seconds when a wide written-amount line makes the decoder run to its length limit. Show a spinner and set the client timeout above 120 s.

## Privacy
- Do not store uploaded images in localStorage or IndexedDB, or send them to analytics.
- Do not log `raw_text` to the console in production builds.
- Use only synthetic or consented images in the demo; no real customer cheques.

## Configuration
The backend allows CORS from `http://localhost:5173` and `http://127.0.0.1:5173` by default, which suits a Vite dev server. Change `CV_CORS_ORIGINS` on the backend for any other origin.
