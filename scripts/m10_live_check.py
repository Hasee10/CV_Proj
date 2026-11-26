"""M10-A live HTTP check against a running server (default http://127.0.0.1:8000). Dev-split images only.
Writes artifacts/M10/LIVE_HTTP_CHECK.json and openapi.json. Usage:
  .venv\\Scripts\\python.exe -X utf8 -I scripts\\m10_live_check.py [--base URL]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_baseline as rb  # noqa: E402

ENT = {e["id"]: e for e in rb.load_entries("dev")}


def png(i):
    return (f"{i}.png", (ROOT / ENT[i]["file"]).read_bytes(), "image/png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base, timeout=300)
    checks = []

    def call(name, method, path, expect, **kw):
        t0 = time.perf_counter()
        r = c.request(method, path, **kw)
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:200]
        ok = r.status_code == expect
        checks.append({"name": name, "request": f"{method} {path}", "status": r.status_code, "expected": expect, "ok": ok,
                       "client_seconds": round(time.perf_counter() - t0, 3), "x_request_id": r.headers.get("x-request-id"),
                       "response": body if path != "/openapi.json" else {"paths": sorted(body["paths"])}})
        return body

    call("health", "GET", "/health", 200)
    call("model_info", "GET", "/api/model-info", 200)
    call("docs_page", "GET", "/docs", 200)
    spec = call("openapi", "GET", "/openapi.json", 200)
    (ROOT / "openapi.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")
    call("recognize_numeric_proposed_synthetic", "POST", "/api/recognize", 200,
         files={"image": png("SYN_0001_num")}, data={"field_type": "numeric", "mode": "proposed"})
    call("recognize_numeric_baseline_synthetic", "POST", "/api/recognize", 200,
         files={"image": png("SYN_0001_num")}, data={"field_type": "numeric", "mode": "baseline"})
    call("recognize_written_genuine", "POST", "/api/recognize", 200,
         files={"image": png("GNHKP_eng_EU_117_w051")}, data={"field_type": "written"})
    call("verify_two_genuine_crops", "POST", "/api/verify", 200,
         files={"numeric_image": png("GNHKP_eng_EU_310_w021"), "written_image": png("GNHKP_eng_EU_117_w051")})
    num, wr = ENT["SYN_0001_num"], ENT["SYN_0001_words"]
    src = ROOT / num["source_file"]
    W, H = Image.open(src).size
    roi = lambda b: json.dumps([round(b[0] / W, 6), round(b[1] / H, 6), round(b[2] / W, 6), round(b[3] / H, 6)])
    call("verify_full_synthetic_cheque_with_rois", "POST", "/api/verify", 200,
         files={"cheque_image": ("cheque.jpg", src.read_bytes(), "image/jpeg")},
         data={"numeric_roi": roi(num["crop_box_xyxy"]), "written_roi": roi(wr["crop_box_xyxy"]), "mode": "proposed"})
    call("error_gif_rejected", "POST", "/api/recognize", 415, files={"image": ("x.gif", b"GIF89a" + b"\0" * 32, "image/gif")},
         data={"field_type": "numeric"})
    call("error_bad_roi", "POST", "/api/verify", 422, files={"cheque_image": ("cheque.jpg", src.read_bytes(), "image/jpeg")},
         data={"numeric_roi": "[0.9, 0.1, 0.2, 0.3]", "written_roi": "[0, 0, 1, 1]"})
    call("error_bad_field_type", "POST", "/api/recognize", 422, files={"image": png("SYN_0001_num")}, data={"field_type": "cheque"})
    call("benchmark_saved_results", "GET", "/api/benchmark", 200)
    out = {"base_url": a.base, "server": "uvicorn backend.app:app (real checkpoint, CPU)", "images": "dev split only (synthetic + GNHK)",
           "passed": sum(x["ok"] for x in checks), "total": len(checks), "checks": checks}
    (ROOT / "artifacts/M10").mkdir(parents=True, exist_ok=True)
    (ROOT / "artifacts/M10/LIVE_HTTP_CHECK.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for x in checks:
        r = x["response"] if isinstance(x["response"], dict) else {}
        print(f"{'ok ' if x['ok'] else 'BAD'} {x['status']} {x['name']} {r.get('decision', '')} {r.get('raw_text', '')} "
              f"{(r.get('numeric') or {}).get('raw_text', '')} {(r.get('written') or {}).get('raw_text', '')} {(r.get('error') or {}).get('code', '')}")
    print(f"{out['passed']}/{out['total']} passed")
    return 0 if out["passed"] == out["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
