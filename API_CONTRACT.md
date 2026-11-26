# ChequeVerify API contract (v0.1.0, M9-A)

Base URL for local use: `http://127.0.0.1:8000`. The machine-readable schema is [openapi.json](openapi.json). Interactive docs are served at `/docs` (Swagger UI) and `/redoc`. FastAPI generates `openapi.json`. It lists only the 200 and 422 responses, and its 422 schema is FastAPI's default validation body. The error bodies the server actually returns follow the shape under Errors below.

Every request and response example referenced below was captured from a real request to the real checkpoint, run by `tests/test_backend_integration.py`. Those files sit in [artifacts/M10/examples/](artifacts/M10/examples/). Nothing in them was typed by hand.

## Conventions
- Uploads use `multipart/form-data`. Only `image/png` and `image/jpeg` are accepted. The first bytes must match the declared type.
- Limits (defaults; see [.env.example](.env.example)):
  - 8 MiB per file;
  - 6000 px on the longest side;
  - 24 million pixels;
  - at least 8 px on each side.
- Amounts are returned as decimal **strings** with two places (`"25000.00"`), never as floats. `null` means the text did not parse.
- `beam_log_probability` is the beam-search score of the hypothesis. It is not a calibrated confidence. Do not display it as a percentage.
- Each response carries an `X-Request-ID` header. JSON bodies include the same `request_id`.
- Images are processed in memory and dropped when the response is sent. Logs hold only request id, path, status and latency.

## Errors
Every error has the same shape:
```json
{"error": {"code": "content_mismatch", "message": "image: file content does not match its declared type", "request_id": "…"}}
```
| status | code | when |
|---|---|---|
| 413 | `file_too_large`, `image_too_large` | byte, side or pixel limit exceeded |
| 415 | `unsupported_media_type`, `content_mismatch` | wrong MIME type, or bytes that do not match it |
| 422 | `undecodable_image`, `image_too_small`, `invalid_roi`, `roi_too_small`, `invalid_parameter`, `invalid_input_combination`, `invalid_request` | input validation |
| 503 | `model_unavailable` | checkpoint missing or failed its hash check |
| 503 | `busy` | no inference slot freed within `CV_QUEUE_TIMEOUT_S` (default 30 s, capped at the inference timeout) |
| 504 | `inference_timeout` | recognition exceeded `CV_INFERENCE_TIMEOUT_S` (default 120 s). The response is sent at the deadline. The model call cannot be interrupted, so it keeps running and holds its slot until it finishes; requests in the meantime may get 503 `busy`. |
| 500 | `internal_error` | unexpected; no details are leaked |

Two responses do not use this shape: the 503 body of `GET /health` (see below), and FastAPI's default `{"detail": "Not Found"}` for an unknown path.

Concurrency: `CV_MAX_CONCURRENCY` (default 1) model calls run at a time. A waiting request never waits longer than the inference timeout, so an abandoned request never starts a model call later. Cancelling a request on the client does not stop a model call that has already started.

## Endpoints

### `GET /health`
- `200 {"status": "ok", "model_loaded": true}` when the model is loaded.
- `503 {"status": "model_unavailable", "model_loaded": false}` otherwise.

Example: `health.json`.

### `GET /api/model-info`
Returns:
- the checkpoint SHA-256, the upstream commit and the parameter count (6,385,537);
- the dictionary, preprocessing and decoding settings;
- the available modes, the frozen M7 configuration and the default mode;
- a list of stated limitations.

Example: `model_info.json`.

### `POST /api/recognize`
| form field | required | values |
|---|---|---|
| `image` | yes | PNG/JPEG crop of one amount field |
| `field_type` | yes | `numeric` or `written` |
| `mode` | no | `baseline` or `proposed`; default = `default_mode` from model-info |

Response fields:
- `raw_text`: the decoder output, unchanged;
- `parsed_value`: string or `null`;
- `parse_status`: `parsed` or `unparseable`;
- `beam_log_probability`;
- `preprocessing`: what the proposed mode did, including the estimated text height and scale;
- `model_input_shape`;
- `latency_seconds` {preprocess, queue_wait, inference, total}: `queue_wait` is the time spent waiting for a free inference slot;
- `image` {width, height};
- `request_id`.

Parsing follows strict grammars:
- **numeric:** ASCII digits; optional `Rs`, `Rs.` or `PKR`; international or South Asian grouping; exactly two decimals if a fraction is present; optional `/-`.
- **written:** English words, optional "Rupees" and "Only", optional "and … Paisa".

Anything else gives `null`. No digit repair or spelling correction is applied.

Examples: `recognize_numeric_baseline.json`, `recognize_numeric_proposed.json`, `error_content_mismatch.json`, `error_model_unavailable.json`.

### `POST /api/verify`
Send exactly one of two input forms. `mode` is optional in both.
1. **Two field images:** `numeric_image` and `written_image`.
2. **Cheque image with user-drawn boxes:** `cheque_image`, `numeric_roi` and `written_roi`. Each ROI is a JSON string `[x0, y0, x1, y1]`, normalised to 0..1 against the uploaded image after EXIF rotation, with `x0 < x1` and `y0 < y1`. The server does not detect fields itself.

The response has `decision`, `reasons` (a list of strings), `mode`, `numeric` and `written` (each a recognize-shaped result without the `image` and `request_id` fields), `rois` (pixel boxes, ROI mode only), `total_latency_seconds`, `notice` and `request_id`.

| decision | rule |
|---|---|
| `accept` | both values parse and are equal |
| `flag` | both values parse and differ |
| `review` | either value is `null` (unreadable, unsupported currency, malformed text) |

`accept` only means the two recognised values agree. It does not show that the cheque is authentic or that recognition was correct. A human must review every result.

The two recognitions run one after the other, each with its own timeout. Set the client timeout to at least twice `CV_INFERENCE_TIMEOUT_S`.

Examples: `verify_two_images_baseline.json`, `verify_cheque_rois_baseline.json`. Live responses for the three demo sheets in `data/demo/` (accept, flag, review) are in `artifacts/M10/LIVE_HTTP_CHECK.json`.

### `GET /api/benchmark`
Returns the saved locked-test comparison from `artifacts/M8/COMPARATIVE_METRICS.json`. It is never recomputed on request, and it answers `404 benchmark_unavailable` if the file is missing.
