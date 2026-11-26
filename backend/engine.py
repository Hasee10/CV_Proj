"""Recognition engine: loads the frozen LoGo-HTR checkpoint once and runs baseline or proposed (ATHN) recognition.

Reuses scripts/smoke_inference.py (loader, upstream transform), scripts/athn.py (proposed preprocessing) and
scripts/eval_metrics.py (strict amount grammars, accept/flag/review rule). No digit repair, no spelling correction,
and the beam score is reported only as an uncalibrated log-probability.
"""
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import athn  # noqa: E402
import eval_metrics as em  # noqa: E402
import run_baseline as rb  # noqa: E402
import smoke_inference as si  # noqa: E402

FROZEN_CONFIG = ROOT / "artifacts/M7/FROZEN_CONFIG.json"
UPSTREAM_COMMIT = "9eaea5fe"
MODES = ("baseline", "proposed")
FIELDS = ("numeric", "written")


class ModelUnavailable(RuntimeError):
    pass


class EngineBusy(RuntimeError):
    pass


class Engine:
    def __init__(self, max_concurrency: int = 1, torch_threads: int | None = None, queue_timeout: float = 30.0):
        self.queue_timeout = queue_timeout
        self.model = self.vocab = self.load_error = None
        self.report: dict = {}
        self.sem = threading.BoundedSemaphore(max_concurrency)
        self.torch_threads = torch_threads
        frozen = json.loads(FROZEN_CONFIG.read_text(encoding="utf-8")) if FROZEN_CONFIG.exists() else {}
        self.frozen = frozen
        self.proposed_cfg = frozen.get("method_config")
        self.default_mode = frozen.get("backend_default_mode", "baseline")

    def load(self):
        try:
            import torch
            if self.torch_threads:
                torch.set_num_threads(self.torch_threads)
            sys.path.insert(0, str(si.UPSTREAM))
            self.vocab = si.install_vocab(rb.DICT).vocab
            t0 = time.perf_counter()
            self.model = si.load_model(self.report)
            self.report["load_seconds"] = round(time.perf_counter() - t0, 2)
        except Exception as ex:  # checkpoint missing, hash mismatch, import failure -> endpoints answer 503
            self.model, self.load_error = None, f"{type(ex).__name__}"
        return self

    @property
    def ready(self) -> bool:
        return self.model is not None

    def info(self) -> dict:
        return {"model": "LoGo-HTR downstream checkpoint (official release, unmodified weights)",
                "checkpoint_sha256": si.CKPT_SHA256, "upstream_commit": UPSTREAM_COMMIT,
                "parameter_count": self.report.get("parameter_count"), "dictionary": rb.DICT,
                "preprocessing": rb.PREPROC, "decoding": rb.DECODE, "device": "cpu",
                "modes": {"baseline": "upstream transform only",
                          "proposed": {"method": "ATHN (adaptive text-height normalisation, training-free)",
                                       "config": self.proposed_cfg, "status": self.frozen.get("status")}},
                "default_mode": self.default_mode, "ready": self.ready,
                "limitations": ["research prototype for human review, not certified bank clearing software",
                                "score is an uncalibrated beam log-probability, not a confidence",
                                "an 'accept' decision means the two recognised values agree; it is not proof of authenticity",
                                "supported currency markers: Rs, Rs., PKR or none; anything else is routed to review"]}

    def recognize(self, rgb, field: str, mode: str) -> dict:
        if not self.ready:
            raise ModelUnavailable("model not loaded")
        if mode == "proposed" and not self.proposed_cfg:
            raise ValueError("proposed mode is not configured (no frozen M7 configuration)")
        import torch
        t0 = time.perf_counter()
        img, meta = (athn.apply(rgb, self.proposed_cfg) if mode == "proposed"
                     else (rgb, {"method": "baseline", "applied": False, "path": "identity"}))
        t1 = time.perf_counter()
        if not self.sem.acquire(timeout=self.queue_timeout):
            raise EngineBusy("all inference slots busy")
        try:
            with torch.inference_mode():
                x, m = si.preprocess_array(img)
                hyp = self.model.approximate_joint_search(x, m)[0]
        finally:
            self.sem.release()
        t2 = time.perf_counter()
        text = "".join(self.vocab.indices2words(hyp.seq))
        value = em.numeric_value(text) if field == "numeric" else em.words_value(text)
        return {"field_type": field, "mode": mode, "raw_text": text, "parsed_value": None if value is None else f"{value:.2f}",
                "parse_status": "parsed" if value is not None else "unparseable",
                "beam_log_probability": round(float(hyp.score), 4),
                "preprocessing": {k: v for k, v in meta.items() if k in ("method", "applied", "path", "scale",
                                                                          "estimated_text_height", "input_hw", "output_hw")},
                "model_input_shape": list(x.shape), "latency_seconds": {"preprocess": round(t1 - t0, 4),
                                                                        "inference": round(t2 - t1, 4), "total": round(t2 - t0, 4)},
                "_value": value}


def decision_reasons(num, wr) -> tuple[str, list[str]]:
    d = em.decide(num["_value"], wr["_value"])
    reasons = []
    if num["_value"] is None:
        reasons.append("numeric_amount_unparseable: recognised text does not satisfy the strict numeric grammar "
                       "(recognition error, unsupported currency or malformed grouping)")
    if wr["_value"] is None:
        reasons.append("written_amount_unparseable: recognised text does not satisfy the strict English amount grammar")
    if d == "accept":
        reasons.append("values_agree: recognised numeric and written values are equal")
    if d == "flag":
        reasons.append(f"values_disagree: numeric {num['parsed_value']} != written {wr['parsed_value']}")
    return d, reasons
