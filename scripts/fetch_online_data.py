"""M4-ONLINE: fetch the online evaluation sources (small, integrity-checked, no account or login needed).

  cvl   -> CVL Digit Strings TRAIN (ICDAR 2013 HDSRC, Zenodo 1492173, CC-BY-NC-4.0, 15.8 MB, MD5-checked)
  hf    -> SYNTHETIC cheque images, test split of arunchincheti/cheques_data (declared Apache-2.0), cheque rows only,
           via the Hugging Face datasets-server rows API (no pyarrow needed); IAM text-line rows are skipped
GNHK is already cached by fetch_gnhk_test.py.
Usage: .venv\\Scripts\\python.exe -X utf8 -I scripts\\fetch_online_data.py cvl|hf
"""
import ast
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CVL_URL = "https://zenodo.org/records/1492173/files/cvl-strings-train.zip?download=1"
CVL_MD5 = "123167109ed2ef554913bd0a9f4d74ba"
CVL_ZIP = ROOT / "data/public/cvl/cache/cvl-strings-train.zip"
HF_DS, HF_REV = "arunchincheti/cheques_data", "cd9902644033cc2114a240743d94309e5ac26bd2"
HF_DIR = ROOT / "data/synthetic/hf_cheques/cache"


def cvl():
    CVL_ZIP.parent.mkdir(parents=True, exist_ok=True)
    if not CVL_ZIP.exists():
        CVL_ZIP.write_bytes(urllib.request.urlopen(CVL_URL, timeout=300).read())
    md5 = hashlib.md5(CVL_ZIP.read_bytes()).hexdigest()
    if md5 != CVL_MD5:
        print(f"ERROR: MD5 {md5} != {CVL_MD5}", file=sys.stderr)
        return 1
    print(f"ok {CVL_ZIP} md5={md5} sha256={hashlib.sha256(CVL_ZIP.read_bytes()).hexdigest()}")
    return 0


def hf():
    HF_DIR.mkdir(parents=True, exist_ok=True)
    info = json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/{HF_DS}", timeout=60))
    if info.get("sha") != HF_REV:
        print(f"WARNING: dataset revision is now {info.get('sha')}, expected {HF_REV}; per-image SHA-256 still recorded",
              file=sys.stderr)
    rows = []
    for off in range(0, 312, 100):
        u = f"https://datasets-server.huggingface.co/rows?dataset={HF_DS}&config=default&split=test&offset={off}&length=100"
        rows += json.load(urllib.request.urlopen(u, timeout=60))["rows"]
    out = []
    for r in rows:
        if "amt_in" not in r["row"]["answers"]:
            continue  # IAM text-line rows: redistribution of registration-gated data, not used
        p = HF_DIR / f"test_{r['row_idx']:04d}.jpg"
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(r["row"]["image"]["src"], timeout=60).read())
        a = {k: v for d in ast.literal_eval(r["row"]["answers"]) for k, v in d.items()}
        out.append({"row_idx": r["row_idx"], "file": p.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "revision_at_fetch": info.get("sha"), **a})
    (HF_DIR / "rows.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"ok {len(out)} synthetic cheque rows of {len(rows)} test rows -> {HF_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit({"cvl": cvl, "hf": hf}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__) or 2)())
