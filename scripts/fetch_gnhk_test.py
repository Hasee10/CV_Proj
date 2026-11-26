"""Fetch ONLY the GNHK official test archive (test_data.zip) from a pinned CC-BY-4.0 mirror.

The official page (goodnotes.com/gnhk) now redirects to the Goodnotes homepage, so the data is
taken from the Hugging Face mirror staghado/GNHK-Dataset at a pinned revision. Only the byte range
of the inner test_data.zip is downloaded (286 MB compressed); the 724 MB train archive is skipped.
Integrity: CRC-32 and size from the outer zip's central directory, then SHA-256 recorded.
Usage: .venv\\Scripts\\python.exe -I scripts\\fetch_gnhk_test.py
"""
import hashlib
import sys
import urllib.request
import zlib
from pathlib import Path

REV = "eaa67d396fd29b8b04e38d630da79f67db11b212"
URL = f"https://huggingface.co/datasets/staghado/GNHK-Dataset/resolve/{REV}/GNHK-dataset.zip"
# from the outer zip central directory (inspected 2026-11-26): local header at 0, data at 65
DATA_START, COMP_SIZE, SIZE, CRC = 65, 286039365, 285995725, 1897843626
OUT = Path(__file__).resolve().parent.parent / "data" / "public" / "gnhk" / "cache" / "test_data.zip"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL, headers={"Range": f"bytes={DATA_START}-{DATA_START + COMP_SIZE - 1}"})
    d, crc, n, sha = zlib.decompressobj(-15), 0, 0, hashlib.sha256()
    with urllib.request.urlopen(req, timeout=120) as r, open(OUT, "wb") as f:
        while chunk := r.read(1 << 20):
            out = d.decompress(chunk)
            f.write(out)
            crc, n = zlib.crc32(out, crc), n + len(out)
            sha.update(out)
        tail = d.flush()
        f.write(tail)
        crc, n = zlib.crc32(tail, crc), n + len(tail)
        sha.update(tail)
    if (n, crc) != (SIZE, CRC):
        OUT.unlink()
        print(f"ERROR: size/CRC mismatch ({n}, {crc}) != ({SIZE}, {CRC}); file removed", file=sys.stderr)
        return 1
    print(f"ok {OUT} bytes={n} crc32={crc} sha256={sha.hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
