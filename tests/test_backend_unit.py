"""M9-A backend UNIT tests: MOCKED inference (no model loaded). They test HTTP contract, validation and decision logic.
Run: .venv\\Scripts\\python.exe -X utf8 -m pytest tests\\test_backend_unit.py -q
"""
import io
import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import backend.app as ba  # noqa: E402
from backend import engine as be  # noqa: E402


class FakeEngine(be.Engine):
    """Mocked engine: returns scripted text per field instead of running LoGo-HTR."""

    def __init__(self, texts=None, ready=True):
        super().__init__()
        self.texts, self._ready, self.seen = texts or {"numeric": "1,250.00", "written": "One Thousand Two Hundred Fifty"}, ready, []

    @property
    def ready(self):
        return self._ready

    def recognize(self, rgb, field, mode):
        if not self._ready:
            raise be.ModelUnavailable()
        self.seen.append((rgb.shape, field, mode))
        text = self.texts[field]
        v = be.em.numeric_value(text) if field == "numeric" else be.em.words_value(text)
        return {"field_type": field, "mode": mode, "raw_text": text, "parsed_value": None if v is None else f"{v:.2f}",
                "parse_status": "parsed" if v is not None else "unparseable", "beam_log_probability": -1.0,
                "preprocessing": {}, "model_input_shape": [1, 3, 32, 64],
                "latency_seconds": {"preprocess": 0.0, "inference": 0.01, "total": 0.01}, "_value": v}


def png(w=120, h=40, fmt="PNG"):
    b = io.BytesIO()
    Image.fromarray(np.full((h, w, 3), 255, np.uint8)).save(b, fmt)
    return b.getvalue()


def client(**kw):
    eng = FakeEngine(**kw)
    return TestClient(ba.create_app(engine=eng, load_model=False)), eng


def files(**kv):
    return {k: (f"{k}.png", v, "image/png") for k, v in kv.items()}


def test_health_and_503_when_model_missing():
    c, _ = client()
    assert c.get("/health").json() == {"status": "ok", "model_loaded": True}
    c2, _ = client(ready=False)
    assert c2.get("/health").status_code == 503
    r = c2.post("/api/recognize", files=files(image=png()), data={"field_type": "numeric"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "model_unavailable"


def test_recognize_ok_and_no_private_fields():
    c, eng = client()
    r = c.post("/api/recognize", files=files(image=png()), data={"field_type": "numeric", "mode": "baseline"})
    j = r.json()
    assert r.status_code == 200 and j["parsed_value"] == "1250.00" and "_value" not in j and r.headers["X-Request-ID"]
    assert eng.seen == [((40, 120, 3), "numeric", "baseline")]


@pytest.mark.parametrize("data,code", [({"field_type": "amount"}, "invalid_parameter"),
                                       ({"field_type": "numeric", "mode": "turbo"}, "invalid_parameter"),
                                       ({}, "invalid_request")])
def test_recognize_rejects_bad_parameters(data, code):
    c, _ = client()
    r = c.post("/api/recognize", files=files(image=png()), data=data)
    assert r.status_code == 422 and r.json()["error"]["code"] == code


def test_upload_validation():
    c, _ = client()
    bad = [(("x.gif", b"GIF89a....", "image/gif"), 415, "unsupported_media_type"),
           (("x.png", b"\xff\xd8\xff" + png()[3:], "image/png"), 415, "content_mismatch"),
           (("x.png", b"\x89PNG\r\n\x1a\n" + b"garbage" * 10, "image/png"), 422, "undecodable_image"),
           (("x.png", png(4, 4), "image/png"), 422, "image_too_small"),
           (("x.png", png(ba.MAX_SIDE + 1, 10), "image/png"), 413, "image_too_large")]
    for f, status, code in bad:
        r = c.post("/api/recognize", files={"image": f}, data={"field_type": "numeric"})
        assert (r.status_code, r.json()["error"]["code"]) == (status, code), (f[0], r.json())
    big = b"\x89PNG\r\n\x1a\n" + b"0" * ba.MAX_BYTES
    r = c.post("/api/recognize", files={"image": ("x.png", big, "image/png")}, data={"field_type": "numeric"})
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"
    jpg = c.post("/api/recognize", files={"image": ("x.jpg", png(fmt="JPEG"), "image/jpeg")}, data={"field_type": "written"})
    assert jpg.status_code == 200


@pytest.mark.parametrize("texts,decision", [
    ({"numeric": "1,250.00", "written": "One Thousand Two Hundred Fifty"}, "accept"),
    ({"numeric": "Rs. 1,250/-", "written": "One Thousand Two Hundred Fifty Only"}, "accept"),
    ({"numeric": "1,250.00", "written": "One Thousand Two Hundred"}, "flag"),
    ({"numeric": "$1,250", "written": "One Thousand Two Hundred Fifty"}, "review"),  # unsupported currency
    ({"numeric": "1,25O", "written": "One Thousand Two Hundred Fifty"}, "review"),  # no digit repair (letter O)
    ({"numeric": "1250", "written": "onethousand"}, "review")])
def test_verify_decisions(texts, decision):
    c, _ = client(texts=texts)
    r = c.post("/api/verify", files=files(numeric_image=png(), written_image=png()))
    j = r.json()
    assert r.status_code == 200 and j["decision"] == decision and j["reasons"] and "not proof of authenticity" in j["notice"]


def test_verify_roi_workflow_and_validation():
    c, eng = client()
    sheet = png(1000, 400)
    ok = c.post("/api/verify", files=files(cheque_image=sheet),
                data={"numeric_roi": "[0.7, 0.3, 0.95, 0.45]", "written_roi": "[0.1, 0.4, 0.6, 0.55]"})
    assert ok.status_code == 200 and ok.json()["rois"] == {"numeric_px": [700, 120, 950, 180], "written_px": [100, 160, 600, 220]}
    assert [s[0] for s in eng.seen] == [(60, 250, 3), (60, 500, 3)]
    for roi in ["[0.5, 0.1, 0.4, 0.2]", "[0, 0, 1.2, 1]", "[0,0,1]", "nope", "[true, 0, 1, 1]", "[0.1, 0.1, 0.105, 0.2]"]:
        r = c.post("/api/verify", files=files(cheque_image=sheet), data={"numeric_roi": roi, "written_roi": "[0,0,1,1]"})
        assert r.status_code == 422 and r.json()["error"]["code"] in ("invalid_roi", "roi_too_small"), roi
    mixed = c.post("/api/verify", files=files(cheque_image=sheet, numeric_image=png()), data={"numeric_roi": "[0,0,1,1]",
                                                                                            "written_roi": "[0,0,1,1]"})
    assert mixed.status_code == 422 and mixed.json()["error"]["code"] == "invalid_input_combination"
    assert c.post("/api/verify", files=files(numeric_image=png())).json()["error"]["code"] == "invalid_input_combination"


def test_decimal_values_not_float():
    num = be.em.numeric_value("12,34,567.10")
    assert isinstance(num, Decimal) and str(num) == "1234567.10"
    assert be.em.decide(Decimal("0.1") + Decimal("0.2"), Decimal("0.3")) == "accept"


def test_benchmark_and_openapi():
    c, _ = client()
    r = c.get("/api/benchmark")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert r.json()["source"] == "artifacts/M8/COMPARATIVE_METRICS.json"
    paths = c.get("/openapi.json").json()["paths"]
    assert {"/health", "/api/model-info", "/api/recognize", "/api/verify", "/api/benchmark"} <= set(paths)


def test_busy_and_timeout_mapping(monkeypatch):
    c, eng = client()

    def busy(*a):
        raise be.EngineBusy()
    monkeypatch.setattr(eng, "recognize", busy)
    assert c.post("/api/recognize", files=files(image=png()), data={"field_type": "numeric"}).json()["error"]["code"] == "busy"
    import time

    def slow(*a):
        time.sleep(0.3)
    monkeypatch.setattr(eng, "recognize", slow)
    monkeypatch.setattr(ba, "TIMEOUT_S", 0.05)
    r = c.post("/api/recognize", files=files(image=png()), data={"field_type": "numeric"})
    assert r.status_code == 504 and r.json()["error"]["code"] == "inference_timeout"


def test_cors_configured_origin_only():
    c, _ = client()
    ok = c.options("/api/recognize", headers={"Origin": ba.CORS[0], "Access-Control-Request-Method": "POST"})
    bad = c.options("/api/recognize", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == ba.CORS[0]
    assert "access-control-allow-origin" not in bad.headers
