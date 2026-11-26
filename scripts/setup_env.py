"""One-command environment setup and self-check for the ChequeVerify backend (standard library only).

Run from the repository root with Python 3.11:
    Windows:  py -3.11 scripts/setup_env.py
    other:    python3.11 scripts/setup_env.py        (only Windows 11 has been tested)

Safe to run again at any time: every step checks first and only does what is missing.
  1. Python 3.11 check
  2. .venv created, pinned packages installed (requirements-inference.txt + requirements-backend.txt)
  3. upstream LoGo-HTR code at the pinned commit in third_party/LoGoHTR (cloned if absent, verified if present)
  4. checkpoint in models/logo_htr/ (downloaded if absent) and its SHA-256 verified
  5. git commit guard enabled (core.hooksPath = .githooks) when this folder is a git clone
  6. frozen files verified, backend tests run: 20 mocked unit tests + 7 integration tests on the real checkpoint
Options: --skip-tests (steps 1-5 only), --with-analysis (also install matplotlib for research figures).
"""
import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_URL = "https://github.com/shreemitra/LoGoHTR"
UPSTREAM_COMMIT = "9eaea5fe52e908ebf3b625ca4c05da3d1905a6af"
CKPT = ROOT / "models/logo_htr/Downstream_Full_Model_Best.ckpt"
CKPT_URL = ("https://huggingface.co/Shree10/LoGo-HTR/resolve/64439ca9edfbf58e3007c2bb6af17559bcf2d29e/"
            "Downstream_Full_Model_Best.ckpt")
CKPT_SHA256 = "25db3a51f70a08cd5cbbf88409470bc4b37821aff95bc5ee6ab89e1e4298c432"
WIN = os.name == "nt"
VENV_PY = ROOT / (".venv/Scripts/python.exe" if WIN else ".venv/bin/python")


def step(n, msg):
    print(f"\n[{n}/6] {msg}", flush=True)


def fail(msg):
    print(f"\nSETUP FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, **kw):
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if r.returncode != 0:
        fail(f"command failed with exit code {r.returncode}: {' '.join(str(c) for c in cmd)}")
    return r


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def python_check():
    step(1, "Python version")
    if sys.version_info[:2] != (3, 11):
        fail(f"Python 3.11 is required (this is {sys.version.split()[0]}). On Windows run: py -3.11 scripts/setup_env.py")
    print(f"  ok: Python {sys.version.split()[0]} ({sys.executable})")


def packages(with_analysis):
    step(2, "virtual environment and pinned packages")
    if not VENV_PY.exists():
        print("  creating .venv ...")
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    reqs = ["requirements-inference.txt", "requirements-backend.txt"] + (["requirements-analysis.txt"] if with_analysis else [])
    stamp = ROOT / ".venv/.chequeverify-requirements.sha256"
    digest = hashlib.sha256(b"".join((ROOT / r).read_bytes() for r in reqs)).hexdigest()
    if stamp.exists() and stamp.read_text().strip() == digest:
        print("  ok: packages already installed for these requirement files")
        return
    if sys.platform == "darwin":
        print("  warning: macOS is untested; the pinned '+cpu' torch wheels do not exist for macOS")
    run([VENV_PY, "-m", "pip", "install", "--disable-pip-version-check", *sum((["-r", r] for r in reqs), [])])
    run([VENV_PY, "-m", "pip", "check"])
    stamp.write_text(digest)


def upstream():
    step(3, f"upstream LoGo-HTR code at {UPSTREAM_COMMIT[:8]}")
    dest = ROOT / "third_party/LoGoHTR"
    if not shutil.which("git"):
        fail("git is not installed or not on PATH")
    if not dest.exists():
        run(["git", "clone", UPSTREAM_URL, dest])
        run(["git", "-C", dest, "checkout", "-q", UPSTREAM_COMMIT])
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != UPSTREAM_COMMIT:
        fail(f"third_party/LoGoHTR is at {head or 'unknown'}, expected {UPSTREAM_COMMIT}. "
             f"Run: git -C third_party/LoGoHTR checkout {UPSTREAM_COMMIT}")
    dirty = subprocess.run(["git", "-C", str(dest), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    if dirty:
        fail("third_party/LoGoHTR has local modifications; the upstream code must stay unmodified. "
             "Restore it with: git -C third_party/LoGoHTR checkout -- .")
    print("  ok: pinned commit, unmodified")


def checkpoint():
    step(4, "checkpoint and SHA-256")
    if not CKPT.exists():
        CKPT.parent.mkdir(parents=True, exist_ok=True)
        part = CKPT.with_suffix(".part")
        print(f"  downloading {CKPT_URL}")
        with urllib.request.urlopen(CKPT_URL, timeout=60) as r, open(part, "wb") as f:
            total, done, shown = int(r.headers.get("Content-Length") or 0), 0, -1
            for chunk in iter(lambda: r.read(1 << 20), b""):
                f.write(chunk)
                done += len(chunk)
                pct = done * 100 // total if total else -1
                if pct >= 0 and pct // 10 != shown:
                    shown = pct // 10
                    print(f"  {pct}%", flush=True)
        if sha256(part) != CKPT_SHA256:
            fail(f"downloaded checkpoint has the wrong SHA-256; the bad file was kept as {part.name}")
        part.replace(CKPT)
    got = sha256(CKPT)
    if got != CKPT_SHA256:
        fail(f"{CKPT.relative_to(ROOT)} has SHA-256 {got}, expected {CKPT_SHA256}. Delete it and rerun this script.")
    print("  ok: " + CKPT_SHA256)


def hooks():
    step(5, "git commit guard")
    if not (ROOT / ".git").exists():
        print("  skipped: this folder is not a git clone (for example an extracted archive). "
              "Clone from GitHub to commit; this script then enables the guard.")
        return
    run(["git", "config", "core.hooksPath", ".githooks"])
    print("  ok: commits that touch frozen files are now refused (see CLAUDE.md)")


def checks():
    step(6, "frozen-file check and backend tests (about 1 minute)")
    run([VENV_PY, "scripts/guard.py", "--verify"])
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    for suite in ("tests/test_backend_unit.py", "tests/test_backend_integration.py"):
        run([VENV_PY, "-X", "utf8", "-m", "pytest", suite, "-q", "-p", "no:cacheprovider", "-W", "ignore::DeprecationWarning"], env=env)


def main():
    args = set(sys.argv[1:])
    unknown = args - {"--skip-tests", "--with-analysis"}
    if unknown:
        fail(f"unknown option(s): {sorted(unknown)}")
    print(f"ChequeVerify environment setup in {ROOT}")
    python_check()
    packages("--with-analysis" in args)
    upstream()
    checkpoint()
    hooks()
    if "--skip-tests" in args:
        print("\n[6/6] skipped (--skip-tests)")
    else:
        checks()
    start = r".venv\Scripts\python.exe" if WIN else ".venv/bin/python"
    print(f"""
SETUP COMPLETE. Start the backend with:
    {start} -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
Then check http://127.0.0.1:8000/health (expect "model_loaded": true) and http://127.0.0.1:8000/docs.""")


if __name__ == "__main__":
    main()
