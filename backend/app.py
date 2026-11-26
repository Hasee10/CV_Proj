"""ChequeVerify FastAPI backend (academic prototype for human review).

Start: .venv\\Scripts\\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
Images are processed in memory only: nothing is written to disk and nothing is retained after the response.
Logs record request id, path, status and latency only (never image bytes or recognised text).
"""
import asyncio
import io
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from backend.engine import FIELDS, MODES, ROOT, Engine, EngineBusy, ModelUnavailable, decision_reasons

log = logging.getLogger("chequeverify")


def env(name, default, cast=str):
    return cast(os.environ.get(name, default))


MAX_BYTES = env("CV_MAX_UPLOAD_BYTES", 8 * 1024 * 1024, int)
MAX_SIDE = env("CV_MAX_IMAGE_SIDE", 6000, int)
MAX_PIXELS = env("CV_MAX_IMAGE_PIXELS", 24_000_000, int)
MIN_SIDE = 8
TIMEOUT_S = env("CV_INFERENCE_TIMEOUT_S", 120.0, float)
CORS = [o.strip() for o in env("CV_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
ALLOWED = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
Image.MAX_IMAGE_PIXELS = MAX_PIXELS  # PIL refuses larger images (decompression-bomb guard)


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def err(status, code, message, rid):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "request_id": rid}})


async def read_image(upload: UploadFile, name: str) -> np.ndarray:
    if upload.content_type not in ALLOWED:
        raise ApiError(415, "unsupported_media_type", f"{name}: only image/png and image/jpeg are accepted")
    data = await upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ApiError(413, "file_too_large", f"{name}: larger than {MAX_BYTES} bytes")
    if not data.startswith(ALLOWED[upload.content_type]):
        raise ApiError(415, "content_mismatch", f"{name}: file content does not match its declared type")
    try:
        im = Image.open(io.BytesIO(data))
        w, h = im.size  # header only, before decoding pixels
        if max(w, h) > MAX_SIDE or w * h > MAX_PIXELS:
            raise ApiError(413, "image_too_large", f"{name}: {w}x{h} exceeds {MAX_SIDE} px per side or {MAX_PIXELS} pixels")
        if min(w, h) < MIN_SIDE:
            raise ApiError(422, "image_too_small", f"{name}: smaller than {MIN_SIDE} px")
        im = ImageOps.exif_transpose(im).convert("RGB")
        return np.array(im)
    except ApiError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError, SyntaxError):
        raise ApiError(422, "undecodable_image", f"{name}: image could not be decoded")


def parse_roi(text: str, name: str):
    try:
        roi = json.loads(text)
        assert isinstance(roi, list) and len(roi) == 4 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in roi)
        x0, y0, x1, y1 = map(float, roi)
        assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1
    except (ValueError, AssertionError, TypeError):
        raise ApiError(422, "invalid_roi", f"{name}: expected JSON [x0, y0, x1, y1] normalised to 0..1 with x0<x1, y0<y1")
    return x0, y0, x1, y1


def crop(rgb, roi, name):
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = round(roi[0] * w), round(roi[1] * h), round(roi[2] * w), round(roi[3] * h)
    if x1 - x0 < MIN_SIDE or y1 - y0 < MIN_SIDE:
        raise ApiError(422, "roi_too_small", f"{name}: region is smaller than {MIN_SIDE} px after scaling")
    return rgb[y0:y1, x0:x1].copy(), [x0, y0, x1, y1]


def check_choice(value, allowed, name):
    if value not in allowed:
        raise ApiError(422, "invalid_parameter", f"{name}: must be one of {list(allowed)}")


def create_app(engine: Engine | None = None, load_model: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        if app.state.engine is None:
            app.state.engine = Engine(max_concurrency=env("CV_MAX_CONCURRENCY", 1, int),
                                      torch_threads=env("CV_TORCH_THREADS", 0, int) or None,
                                      # never wait for a slot longer than the caller waits for the answer, so an
                                      # abandoned request cannot start a model call later
                                      queue_timeout=min(env("CV_QUEUE_TIMEOUT_S", 30.0, float), TIMEOUT_S))
            if load_model:
                await run_in_threadpool(app.state.engine.load)
        yield

    app = FastAPI(title="ChequeVerify API", version="0.1.0", lifespan=lifespan,
                  description="Handwritten cheque amount recognition (LoGo-HTR, frozen checkpoint) and numeric-vs-written "
                              "consistency check. Academic prototype for human review; not certified bank software. "
                              "A match is not proof of authenticity. Scores are uncalibrated.")
    app.state.engine = engine
    app.add_middleware(CORSMiddleware, allow_origins=CORS, allow_methods=["GET", "POST"], allow_headers=["*"])

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        rid = uuid.uuid4().hex[:12]
        request.state.rid = rid
        t0 = time.perf_counter()
        resp = await call_next(request)
        resp.headers["X-Request-ID"] = rid
        log.info("rid=%s %s %s status=%s %.3fs", rid, request.method, request.url.path, resp.status_code, time.perf_counter() - t0)
        return resp

    @app.exception_handler(ApiError)
    async def api_error(request: Request, ex: ApiError):
        return err(ex.status, ex.code, ex.message, request.state.rid)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, ex: RequestValidationError):
        fields = sorted({".".join(str(p) for p in e["loc"][1:]) for e in ex.errors()})
        return err(422, "invalid_request", f"missing or invalid fields: {fields}", request.state.rid)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, ex: Exception):
        log.error("rid=%s unhandled %s", request.state.rid, type(ex).__name__)
        return err(500, "internal_error", "unexpected server error", request.state.rid)

    def engine_or_503(request) -> Engine:
        eng = request.app.state.engine
        if eng is None or not eng.ready:
            raise ApiError(503, "model_unavailable", "the recognition model is not loaded")
        return eng

    async def run(eng, rgb, field, mode):
        try:
            return await asyncio.wait_for(run_in_threadpool(eng.recognize, rgb, field, mode), TIMEOUT_S)
        except asyncio.TimeoutError:
            raise ApiError(504, "inference_timeout",
                           f"recognition exceeded {TIMEOUT_S:g} s. The model call cannot be interrupted and keeps its "
                           "inference slot until it finishes, so new requests may receive 503 busy meanwhile")
        except EngineBusy:
            raise ApiError(503, "busy", "all inference slots are busy; retry later")
        except ModelUnavailable:
            raise ApiError(503, "model_unavailable", "the recognition model is not loaded")
        except ValueError as ex:
            raise ApiError(422, "invalid_parameter", str(ex))

    def public(r):
        return {k: v for k, v in r.items() if not k.startswith("_")}

    @app.get("/health")
    async def health(request: Request):
        eng = request.app.state.engine
        ready = bool(eng and eng.ready)
        return JSONResponse(status_code=200 if ready else 503,
                            content={"status": "ok" if ready else "model_unavailable", "model_loaded": ready})

    @app.get("/api/model-info")
    async def model_info(request: Request):
        eng = request.app.state.engine
        if eng is None:
            raise ApiError(503, "model_unavailable", "engine not initialised")
        return eng.info()

    @app.post("/api/recognize")
    async def recognize(request: Request, image: UploadFile = File(...), field_type: str = Form(...),
                        mode: str | None = Form(None)):
        """Recognise one cropped amount field. field_type: numeric | written. mode: baseline | proposed."""
        eng = engine_or_503(request)
        mode = mode or eng.default_mode
        check_choice(field_type, FIELDS, "field_type")
        check_choice(mode, MODES, "mode")
        rgb = await read_image(image, "image")
        r = await run(eng, rgb, field_type, mode)
        return {**public(r), "image": {"width": rgb.shape[1], "height": rgb.shape[0]}, "request_id": request.state.rid}

    @app.post("/api/verify")
    async def verify(request: Request, mode: str | None = Form(None),
                     numeric_image: UploadFile | None = File(None), written_image: UploadFile | None = File(None),
                     cheque_image: UploadFile | None = File(None),
                     numeric_roi: str | None = Form(None), written_roi: str | None = Form(None)):
        """Either numeric_image + written_image, or cheque_image + numeric_roi + written_roi
        (user-selected normalised boxes [x0, y0, x1, y1])."""
        eng = engine_or_503(request)
        mode = mode or eng.default_mode
        check_choice(mode, MODES, "mode")
        rois = None
        if numeric_image and written_image and not cheque_image:
            num_rgb, wr_rgb = await read_image(numeric_image, "numeric_image"), await read_image(written_image, "written_image")
        elif cheque_image and numeric_roi and written_roi and not (numeric_image or written_image):
            nr, wr = parse_roi(numeric_roi, "numeric_roi"), parse_roi(written_roi, "written_roi")
            full = await read_image(cheque_image, "cheque_image")
            (num_rgb, nb), (wr_rgb, wb) = crop(full, nr, "numeric_roi"), crop(full, wr, "written_roi")
            rois = {"numeric_px": nb, "written_px": wb}
        else:
            raise ApiError(422, "invalid_input_combination",
                           "send numeric_image + written_image, or cheque_image + numeric_roi + written_roi")
        num = await run(eng, num_rgb, "numeric", mode)
        wr = await run(eng, wr_rgb, "written", mode)
        decision, reasons = decision_reasons(num, wr)
        return {"decision": decision, "reasons": reasons, "mode": mode, "numeric": public(num), "written": public(wr),
                "rois": rois, "total_latency_seconds": round(num["latency_seconds"]["total"] + wr["latency_seconds"]["total"], 4),
                "notice": "decision compares recognised values only; 'accept' is not proof of authenticity; review is required "
                          "whenever either value cannot be parsed",
                "request_id": request.state.rid}

    @app.get("/api/benchmark")
    async def benchmark():
        """Saved locked-test results (artifacts/M8). Never recomputed on request."""
        p = ROOT / "artifacts/M8/COMPARATIVE_METRICS.json"
        if not p.exists():
            raise ApiError(404, "benchmark_unavailable", "no saved benchmark results")
        return {"source": "artifacts/M8/COMPARATIVE_METRICS.json", **json.loads(p.read_text(encoding="utf-8"))}

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
app = create_app()
