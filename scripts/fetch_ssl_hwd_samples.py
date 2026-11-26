"""Fetch a small, rule-selected set of SSL-HWD word images for the M3-A smoke test.

Reads only the first 4 MiB of the official labelled zip (HTTP range request), never the
full 14.5 GB archive. Selection rule is fixed here BEFORE any inference (see RULES).
Usage: .venv\\Scripts\\python.exe -I scripts\\fetch_ssl_hwd_samples.py
"""
import hashlib
import json
import re
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

REVISION = "91b51355f71e1166eb5b1ef3e6c0540463f32008"
URL = ("https://huggingface.co/datasets/Shree10/SSL-HWD-Words/resolve/"
       f"{REVISION}/SSL-HWD-Words(Labeled).zip")
N_BYTES = 4 * 1024 * 1024
OUT = Path(__file__).resolve().parent.parent / "data" / "smoke_samples" / "ssl_hwd"
PREFIX = "SSL-HWD-Words(Labeled)/writer1/"

# Pre-registered rule: walk writer1.csv in row order, take the first k images (present in
# the fetched bytes) whose transcription matches each pattern. Fixed order, no replacement.
RULES = [
    ("numeric", re.compile(r"^[0-9]+$"), 3),
    ("lowercase_word_len5plus", re.compile(r"^[a-z]{5,}$"), 3),
    ("capitalised_word_len5plus", re.compile(r"^[A-Z][a-z]{4,}$"), 2),
    ("alphanumeric_mixed", re.compile(r"^(?=.*[0-9])(?=.*[A-Za-z]).+$"), 2),
]


def parse_local_entries(buf: bytes) -> dict:
    """Stream-parse zip local headers; entries use deflate + data descriptors."""
    files, off = {}, 0
    while off + 30 <= len(buf) and buf[off:off + 4] == b"PK\x03\x04":
        _, flag, meth, _, _, _, csize, _, fl, el = struct.unpack("<HHHHHIIIHH", buf[off + 4:off + 30])
        name = buf[off + 30:off + 30 + fl].decode("utf-8")
        p = off + 30 + fl + el
        if name.endswith("/"):
            off = p + (16 if flag & 8 and buf[p:p + 4] == b"PK\x07\x08" else 0)
            continue
        if not flag & 8:
            raw = buf[p:p + csize]
            files[name] = raw if meth == 0 else zlib.decompress(raw, -15)
            off = p + csize
            continue
        d = zlib.decompressobj(-15)
        data = d.decompress(buf[p:])
        if not d.eof:  # last entry cut off by the byte range
            break
        files[name] = data
        q = len(buf) - len(d.unused_data)
        off = q + (16 if buf[q:q + 4] == b"PK\x07\x08" else 12)
    return files


def main() -> int:
    req = urllib.request.Request(URL, headers={"Range": f"bytes=0-{N_BYTES - 1}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        buf = r.read()
    files = parse_local_entries(buf)
    rows = files[PREFIX + "writer1.csv"].decode("utf-8").splitlines()[1:]
    picked = []
    for cat, pat, k in RULES:
        n = 0
        for row in rows:
            fname, text = row.split(",", 1)
            if n < k and pat.match(text) and (PREFIX + fname) in files:
                picked.append((cat, fname, text))
                n += 1
        if n < k:
            print(f"WARNING: only {n}/{k} samples for {cat}", file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": URL, "dataset_revision": REVISION, "license": "apache-2.0 (dataset card)",
                "bytes_fetched": len(buf), "writer": "writer1", "selection_rules":
                [[c, p.pattern, k] for c, p, k in RULES], "samples": []}
    for i, (cat, fname, text) in enumerate(picked, 1):
        data = files[PREFIX + fname]
        (OUT / fname).write_bytes(data)
        manifest["samples"].append({"id": f"S{i:02d}", "category": cat, "file": f"data/smoke_samples/ssl_hwd/{fname}",
                                    "ground_truth": text, "sha256": hashlib.sha256(data).hexdigest()})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["samples"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
