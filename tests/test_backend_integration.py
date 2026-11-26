"""M9-A backend INTEGRATION tests: GENUINE inference with the real LoGo-HTR checkpoint (CPU, dev-split images only).
Each response is compared with the cached prediction for the same pixels from the M5/M7 offline runs (determinism).
Request/response examples are written to artifacts/M10/examples/ for the API documentation.
Run: .venv\\Scripts\\python.exe -X utf8 -m pytest tests\\test_backend_integration.py -q
"""
import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import backend.app as ba  # noqa: E402
from backend import engine as be  # noqa: E402

EX = ROOT / "artifacts/M10/examples"
M5 = {r["id"]: r for r in json.loads((ROOT / "artifacts/M5_DEV/BASELINE_RESULTS.json").read_text(encoding="utf-8"))["results"]}
ENT = {e["id"]: e for e in be.rb.load_entries("dev")}


def raw(i):
    return (ROOT / ENT[i]["file"]).read_bytes()


def save(name, request, response):
    EX.mkdir(parents=True, exist_ok=True)
    (EX / f"{name}.json").write_text(json.dumps({"request": request, "response": response}, indent=1, ensure_ascii=False),
                                     encoding="utf-8")


@pytest.fixture(scope="module")
def client():
    eng = be.Engine().load()
    assert eng.ready, eng.load_error
    with TestClient(ba.create_app(engine=eng, load_model=False)) as c:
        yield c


def test_health_and_model_info(client):
    h = client.get("/health")
    assert h.status_code == 200 and h.json()["model_loaded"] is True
    info = client.get("/api/model-info").json()
    assert info["parameter_count"] == 6385537 and info["checkpoint_sha256"].startswith("25db3a51")
    save("health", {"method": "GET", "path": "/health"}, h.json())
    save("model_info", {"method": "GET", "path": "/api/model-info"}, info)


def test_recognize_numeric_matches_offline_baseline(client):
    i = "CVL_25000_0021_08"
    r = client.post("/api/recognize", files={"image": (f"{i}.png", raw(i), "image/png")},
                    data={"field_type": "numeric", "mode": "baseline"})
    j = r.json()
    assert r.status_code == 200 and j["raw_text"] == M5[i]["prediction"] == "25000" and j["parsed_value"] == "25000.00"
    save("recognize_numeric_baseline", {"method": "POST", "path": "/api/recognize", "form": {"image": f"{i}.png (CVL dev crop)",
                                        "field_type": "numeric", "mode": "baseline"}}, j)


def test_verify_two_images_matches_offline_pair(client):
    num, wr = "SYN_0001_num", "SYN_0001_words"
    r = client.post("/api/verify", files={"numeric_image": ("n.png", raw(num), "image/png"),
                                          "written_image": ("w.png", raw(wr), "image/png")}, data={"mode": "baseline"})
    j = r.json()
    assert r.status_code == 200
    assert j["numeric"]["raw_text"] == M5[num]["prediction"] and j["written"]["raw_text"] == M5[wr]["prediction"]
    pair = next(p for p in json.loads((ROOT / "artifacts/M5_DEV/PAIR_RESULTS.json").read_text(encoding="utf-8"))["pairs"]
                if p["num_id"] == num and p["words_id"] == wr)
    assert j["decision"] == pair["decision"]
    save("verify_two_images_baseline", {"method": "POST", "path": "/api/verify", "form": {
        "numeric_image": f"{num}.png (synthetic dev crop)", "written_image": f"{wr}.png (synthetic dev crop)", "mode": "baseline"}}, j)


def test_verify_cheque_with_rois_reproduces_crops(client):
    """Paste two genuine dev crops onto a white sheet; the user ROIs select them back pixel-exactly."""
    num, wr = "GNHKP_eng_EU_310_w021", "GNHKP_eng_EU_117_w051"
    a, b = (np.array(Image.open(io.BytesIO(raw(i))).convert("RGB")) for i in (num, wr))
    H, W = 40 + a.shape[0] + 40 + b.shape[0] + 40, 40 + max(a.shape[1], b.shape[1]) + 40
    sheet = np.full((H, W, 3), 255, np.uint8)
    ya, yb = 40, 80 + a.shape[0]
    sheet[ya:ya + a.shape[0], 40:40 + a.shape[1]] = a
    sheet[yb:yb + b.shape[0], 40:40 + b.shape[1]] = b
    buf = io.BytesIO()
    Image.fromarray(sheet).save(buf, "PNG")
    roi = lambda y, im: json.dumps([40 / W, y / H, (40 + im.shape[1]) / W, (y + im.shape[0]) / H])
    form = {"numeric_roi": roi(ya, a), "written_roi": roi(yb, b), "mode": "baseline"}
    r = client.post("/api/verify", files={"cheque_image": ("sheet.png", buf.getvalue(), "image/png")}, data=form)
    j = r.json()
    assert r.status_code == 200, j
    assert j["rois"]["numeric_px"] == [40, ya, 40 + a.shape[1], ya + a.shape[0]]
    assert j["numeric"]["raw_text"] == M5[num]["prediction"] and j["written"]["raw_text"] == M5[wr]["prediction"]
    save("verify_cheque_rois_baseline", {"method": "POST", "path": "/api/verify",
                                         "form": {"cheque_image": f"sheet.png ({W}x{H}, two GNHK dev crops pasted)", **form}}, j)


def test_proposed_mode_matches_offline_method(client):
    if not be.FROZEN_CONFIG.exists():
        pytest.skip("no frozen M7 configuration")
    frozen = json.loads(be.FROZEN_CONFIG.read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in json.loads((ROOT / frozen["dev_results_file"]).read_text(encoding="utf-8"))["results"]}
    i = "SYN_0001_num"
    r = client.post("/api/recognize", files={"image": ("n.png", raw(i), "image/png")}, data={"field_type": "numeric", "mode": "proposed"})
    j = r.json()
    assert r.status_code == 200 and j["raw_text"] == rows[i]["prediction"]
    assert j["preprocessing"]["applied"] == rows[i]["preprocess"]["applied"]
    save("recognize_numeric_proposed", {"method": "POST", "path": "/api/recognize",
                                        "form": {"image": f"{i}.png (synthetic dev crop)", "field_type": "numeric", "mode": "proposed"}}, j)


def test_validation_error_with_real_engine(client):
    r = client.post("/api/recognize", files={"image": ("x.png", b"not an image", "image/png")}, data={"field_type": "numeric"})
    assert r.status_code == 415 and r.json()["error"]["code"] == "content_mismatch"
    save("error_content_mismatch", {"method": "POST", "path": "/api/recognize", "form": {"image": "x.png (12 bytes of text)",
                                    "field_type": "numeric"}}, r.json())


def test_missing_checkpoint_gives_503(monkeypatch):
    monkeypatch.setattr(be.si, "CKPT", ROOT / "models/does_not_exist.ckpt")
    eng = be.Engine().load()
    assert not eng.ready and eng.load_error
    with TestClient(ba.create_app(engine=eng, load_model=False)) as c:
        assert c.get("/health").status_code == 503
        r = c.post("/api/recognize", files={"image": ("x.png", raw("CVL_25000_0021_08"), "image/png")}, data={"field_type": "numeric"})
        assert r.status_code == 503 and r.json()["error"]["code"] == "model_unavailable"
        save("error_model_unavailable", {"method": "POST", "path": "/api/recognize", "note": "server started without checkpoint"},
             r.json())
