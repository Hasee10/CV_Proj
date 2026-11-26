"""Validate dataset manifests before formal evaluation (amended M4-AUDIT 2026-11-26).

Fails (exit 1, passed=false) on any of:
  - empty manifest set; missing required field (id, file, sha256, ground_truth, split, group_id); duplicate id
  - split not in {dev, test, exploratory}; file missing, unreadable or sha256 mismatch
  - source_file present but missing or not matching source_sha256
  - a group_id, writer_id or pair_id spanning splits
  - parent_id that is not among the loaded samples, or whose split differs (stress lineage)
  - cross-split exact duplicate (sha256)
  - cross-split near-duplicate candidate (64-bit dHash, Hamming <= NEAR) not reviewed in --resolved,
    or reviewed as a true duplicate. Candidates are never deleted automatically.
--resolved: JSON list of {"pair": [id_a, id_b], "decision": "not_duplicate"|"duplicate", "reviewer": .., "note": ..}
--out: report path; refuses to overwrite an existing file.
Usage: .venv\\Scripts\\python.exe -I scripts\\validate_manifest.py M.json [M2.json ...] [--resolved R.json] [--out report.json]
"""
import argparse
import hashlib
import json
import sys
from decimal import Decimal
from itertools import combinations
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NEAR = 4
REQUIRED = ("id", "file", "sha256", "ground_truth", "split", "group_id")


def dhash(path: Path) -> int:
    px = Image.open(path).convert("L").resize((9, 8), Image.BILINEAR).tobytes()
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate(samples, resolved=None, root=ROOT):
    errors, ids, src_cache = [], {}, {}
    if not samples:
        errors.append("no samples (empty manifest set)")
    for s in samples:
        miss = [k for k in REQUIRED if k not in s or s[k] is None]
        if miss:
            errors.append(f"{s.get('id', '?')}: missing required field(s) {miss}")
            continue
        if s["id"] in ids:
            errors.append(f"duplicate id {s['id']}")
        ids[s["id"]] = s
        if s["split"] not in ("dev", "test", "exploratory"):
            errors.append(f"{s['id']}: bad split {s['split']}")
        p = root / s["file"]
        if not p.exists():
            errors.append(f"{s['id']}: missing file")
            continue
        if _sha(p) != s["sha256"]:
            errors.append(f"{s['id']}: sha256 mismatch")
        try:
            s["_dhash"] = dhash(p)
        except Exception as e:
            errors.append(f"{s['id']}: unreadable ({type(e).__name__})")
        if s.get("source_file"):
            sp = root / s["source_file"]
            if s["source_file"] not in src_cache:
                src_cache[s["source_file"]] = _sha(sp) if sp.exists() else None
            if src_cache[s["source_file"]] != s.get("source_sha256"):
                errors.append(f"{s['id']}: source_file missing or source_sha256 mismatch")
    good = list(ids.values())
    for key in ("group_id", "writer_id", "pair_id"):
        spans = {}
        for s in good:
            if s.get(key) is not None:
                spans.setdefault(s[key], set()).add(s["split"])
        errors += [f"{key} {k} spans splits {sorted(v)}" for k, v in spans.items() if len(v) > 1]
    for s in good:
        par = s.get("parent_id")
        if par is not None and par not in ids:
            errors.append(f"{s['id']}: parent {par} not in loaded manifests (lineage unverifiable)")
        elif par is not None and ids[par]["split"] != s["split"]:
            errors.append(f"{s['id']}: split differs from parent {par}")
    decisions = {frozenset(r["pair"]): r.get("decision") for r in (resolved or [])}
    exact, near, unresolved = [], [], []
    hashed = [s for s in good if "_dhash" in s]
    for x, y in combinations(hashed, 2):
        if x["split"] == y["split"]:
            continue
        if x["sha256"] == y["sha256"]:
            # only exception: both crops are verified-blank fields (no handwriting) and reviewed as such
            if not (x.get("ground_truth") == y.get("ground_truth") == ""
                    and decisions.get(frozenset((x["id"], y["id"]))) == "blank_field"):
                exact.append([x["id"], y["id"]])
        elif bin(x["_dhash"] ^ y["_dhash"]).count("1") <= NEAR:
            near.append([x["id"], y["id"]])
            d = decisions.get(frozenset((x["id"], y["id"])))
            blank_ok = d == "blank_field" and x.get("ground_truth") == y.get("ground_truth") == ""
            if d != "not_duplicate" and not blank_ok:
                unresolved.append({"pair": [x["id"], y["id"]], "decision": d})
    errors += [f"exact duplicate across splits {p}" for p in exact]
    errors += [f"near-duplicate candidate not cleared {u['pair']} (decision={u['decision']})" for u in unresolved]
    for s in samples:
        s.pop("_dhash", None)
    return {"samples": len(samples),
            "per_split": {k: sum(s.get("split") == k for s in samples) for k in ("dev", "test", "exploratory")},
            "groups": len({s.get("group_id") for s in good}), "near_duplicate_threshold_hamming": NEAR,
            "cross_split_exact_duplicates": exact, "cross_split_near_duplicate_candidates": near,
            "near_duplicates_unresolved": unresolved, "errors": errors, "passed": not errors}


def validate_pairs(pairs, samples):
    """Amount pairs: unique ids; both crops exist and share the pair's split; label agrees with the samples'
    independent gt_value (match iff equal, mismatch iff different, unresolved iff a value is missing);
    natural pairs come from one source document, constructed pairs from two."""
    by, errors, seen = {s["id"]: s for s in samples}, [], set()
    for p in pairs:
        pid = p.get("pair_id")
        if pid in seen:
            errors.append(f"duplicate pair_id {pid}")
        seen.add(pid)
        a, b = by.get(p.get("num_id")), by.get(p.get("words_id"))
        if a is None or b is None:
            errors.append(f"{pid}: missing sample(s)")
            continue
        if not (a["split"] == b["split"] == p.get("split")):
            errors.append(f"{pid}: split mismatch {a['split']}/{b['split']}/{p.get('split')}")
        va, vb = a.get("gt_value"), b.get("gt_value")
        want = "unresolved" if va is None or vb is None else ("match" if Decimal(va) == Decimal(vb) else "mismatch")
        if p.get("label") != want:
            errors.append(f"{pid}: label {p.get('label')} != {want} from gt values")
        natural = str(p.get("construction", "")).startswith("natural")
        if natural != (a.get("group_id") == b.get("group_id")):
            errors.append(f"{pid}: construction {p.get('construction')} inconsistent with source groups")
    labels = {}
    for p in pairs:
        labels[p.get("label")] = labels.get(p.get("label"), 0) + 1
    return {"pairs": len(pairs), "labels": labels, "errors": errors, "passed": bool(pairs) and not errors}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--resolved")
    ap.add_argument("--pairs", help="amount_pairs.json to check against the loaded samples")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.out and Path(a.out).exists():
        print(f"ERROR: {a.out} exists; refusing to overwrite a validation report", file=sys.stderr)
        return 2
    samples = []
    for m in a.manifests:
        samples += json.loads(Path(m).read_text(encoding="utf-8"))["samples"]
    resolved = json.loads(Path(a.resolved).read_text(encoding="utf-8")) if a.resolved else None
    report = {"manifests": a.manifests, "resolved_file": a.resolved, **validate([dict(s) for s in samples], resolved)}
    if a.pairs:
        pr = validate_pairs(json.loads(Path(a.pairs).read_text(encoding="utf-8"))["pairs"], samples)
        report["pair_check"] = pr
        report["passed"] = report["passed"] and pr["passed"]
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cross_split_near_duplicate_candidates"}, indent=1))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
