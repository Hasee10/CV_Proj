"""Rule-based review of cross-split duplicate candidates for the M4-ONLINE benchmarks (automated, NOT human).

Rules (applied only to candidates the validator reports; nothing is deleted):
  - both crops have ground_truth "" (verified blank field, no handwriting)  -> "blank_field"
  - ground-truth transcriptions differ                                    -> "not_duplicate"
  - same non-blank transcription                                          -> left UNRESOLVED (needs visual review)
Usage: .venv\\Scripts\\python.exe -I scripts\\review_duplicates.py OUT.json MANIFEST.json [MANIFEST2.json ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_manifest as vm  # noqa: E402


def main() -> int:
    out, manifests = Path(sys.argv[1]), sys.argv[2:]
    if out.exists():
        print(f"ERROR: {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    samples = [s for m in manifests for s in json.loads(Path(m).read_text(encoding="utf-8"))["samples"]]
    by = {s["id"]: s for s in samples}
    rep = vm.validate([dict(s) for s in samples])
    cands = [u["pair"] for u in rep["near_duplicates_unresolved"]] + rep["cross_split_exact_duplicates"]
    review, left = [], []
    for a, b in cands:
        ga, gb = by[a]["ground_truth"], by[b]["ground_truth"]
        if ga == gb == "":
            review.append({"pair": [a, b], "decision": "blank_field", "basis": "both verified blank fields",
                           "reviewer": "rule (automated, not human)"})
        elif ga != gb:
            review.append({"pair": [a, b], "decision": "not_duplicate",
                           "basis": f"different ground truth: {ga!r} vs {gb!r}", "reviewer": "rule (automated, not human)"})
        else:
            left.append([a, b])
    out.write_text(json.dumps(review, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cands)} candidates: {len(review)} resolved by rule, {len(left)} need visual review {left[:5]}")
    return 0 if not left else 1


if __name__ == "__main__":
    sys.exit(main())
