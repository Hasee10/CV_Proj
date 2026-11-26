"""Protects the frozen research and backend from accidental changes (standard library only).

  python scripts/guard.py --verify   every frozen file still matches FROZEN_MANIFEST.json (byte-exact SHA-256)
  python scripts/guard.py --staged   pre-commit check (installed by scripts/setup_env.py as .githooks/pre-commit)

Commit policy (--staged): only paths under frontend/ and the four status documents may be added, changed or
deleted. Everything else (backend, scripts, tests, artifacts, data, docs, configs) is frozen. Inside the allowed
paths, weights, archives, dependency folders, build output, .env files, files over 5 MB and token-like secrets
are refused. The project owner can still commit deliberately with `git commit --no-verify`; coding agents are
denied that flag in .claude/settings.json.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "FROZEN_MANIFEST.json"
ALLOWED_FILES = {"README.md", "PROJECT_TRACKER.md", "ROADMAP.md", "PROJECT_CONTEXT.md"}
ALLOWED_PREFIX = "frontend/"
BLOCKED_PARTS = {"node_modules", "dist", "build", ".next", "out", "coverage", ".venv", "__pycache__", ".pytest_cache"}
BLOCKED_SUFFIX = (".ckpt", ".pth", ".pt", ".onnx", ".safetensors", ".bin", ".zip", ".7z", ".tar", ".gz")
MAX_BYTES = 5 * 1024 * 1024
SECRET = re.compile(r"hf_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def allowed(path: str) -> bool:
    return path in ALLOWED_FILES or path.startswith(ALLOWED_PREFIX)


def staged() -> int:
    raw = git("diff", "--cached", "--name-status", "-z", "--no-renames").decode("utf-8").split("\0")
    entries = [(raw[i], raw[i + 1]) for i in range(0, len(raw) - 1, 2)]
    problems = []
    for status, path in entries:
        if not allowed(path):
            problems.append(f"{path}: frozen (only frontend/ and {', '.join(sorted(ALLOWED_FILES))} may change)")
            continue
        if status == "D":
            continue
        parts = set(path.split("/"))
        name = path.rsplit("/", 1)[-1]
        if parts & BLOCKED_PARTS:
            problems.append(f"{path}: dependency or build output must not be committed")
        elif path.lower().endswith(BLOCKED_SUFFIX):
            problems.append(f"{path}: model weights or archives must not be committed")
        elif name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            problems.append(f"{path}: environment files must not be committed")
        else:
            blob = git("show", f":{path}")
            if len(blob) > MAX_BYTES:
                problems.append(f"{path}: {len(blob)} bytes is over the 5 MB limit")
            elif SECRET.search(blob.decode("utf-8", "ignore")):
                problems.append(f"{path}: contains something that looks like a secret token or private key")
    if problems:
        print("COMMIT BLOCKED by scripts/guard.py (see CLAUDE.md, 'Protected files'):", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        print("Unstage these paths (git restore --staged <path>) and restore frozen files (git restore <path>).", file=sys.stderr)
        return 1
    return 0


def verify() -> int:
    if not MANIFEST.exists():
        print("guard: FROZEN_MANIFEST.json missing", file=sys.stderr)
        return 1
    files = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    bad = []
    for rel, digest in files.items():
        p = ROOT / rel
        if not p.is_file():
            bad.append(f"missing: {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad.append(f"changed: {rel}")
    if bad:
        print(f"guard: {len(bad)} frozen file(s) differ from FROZEN_MANIFEST.json:", file=sys.stderr)
        for b in bad[:50]:
            print("  - " + b, file=sys.stderr)
        print("Restore them with `git restore <path>` (or `git checkout -- <path>`). Never edit frozen files.", file=sys.stderr)
        return 1
    print(f"guard: all {len(files)} frozen files match FROZEN_MANIFEST.json")
    return 0


def write_manifest() -> int:
    """Maintainer only: record the frozen state of every tracked file outside the allowed paths."""
    paths = [p for p in git("ls-files", "-z").decode("utf-8").split("\0") if p and not allowed(p) and p != MANIFEST.name]
    files = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(paths)}
    MANIFEST.write_text(json.dumps({"note": "SHA-256 of every frozen tracked file; checked by scripts/guard.py --verify",
                                    "files": files}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {MANIFEST.name}: {len(files)} files")
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"--staged": staged, "--verify": verify, "--write-manifest": write_manifest}.get(
        mode, lambda: print(__doc__) or 2)())
