import { useEffect, useRef, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { ArrowRight, Download, Play, Square, UploadCloud } from "lucide-react";
import { api, ApiError } from "../../api/client";
import type {
  FieldResult,
  VerifyResult,
  CaptureRecord,
} from "../../api/results";
import type { useModelStatus } from "../../hooks/useModelStatus";
import { useCaptureContext } from "../../hooks/useSavedCapture";
import { labSamples } from "../../lib/sampleLibrary";
import { recordRun } from "../../lib/sessionRuns";
import { FieldResultCard } from "./ResultDetails";

export function validateUpload(
  file: Pick<File, "type" | "size">,
): string | null {
  if (!["image/png", "image/jpeg"].includes(file.type))
    return "Choose a PNG or JPEG image.";
  if (file.size > 5 * 1024 * 1024) return "Choose an image smaller than 5 MB.";
  if (!file.size) return "This image is empty.";
  return null;
}
function usePreview(file: File | null) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!file) {
      setUrl("");
      return;
    }
    const next = URL.createObjectURL(file);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [file]);
  return url;
}
function UploadField({
  label,
  file,
  onFile,
  disabled,
}: {
  label: string;
  file: File | null;
  onFile: (f: File) => void;
  disabled: boolean;
}) {
  return (
    <label className="lab-upload">
      <UploadCloud size={22} />
      <strong>{label}</strong>
      <span>{file?.name ?? "Choose PNG or JPEG · up to 5 MB"}</span>
      <input
        type="file"
        accept="image/png,image/jpeg"
        aria-label={label}
        disabled={disabled}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onFile(file);
          e.target.value = "";
        }}
      />
    </label>
  );
}
function ResultDownload({ value }: { value: unknown }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    const next = URL.createObjectURL(
      new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
    );
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [value]);
  return (
    <a
      className="lab-download"
      href={url}
      download="chequeverify-response.json"
    >
      <Download size={15} /> Download response
    </a>
  );
}
export function LiveLab({ kind }: { kind: "recognition" | "verification" }) {
  const system = useOutletContext<ReturnType<typeof useModelStatus>>(),
    capture = useCaptureContext();
  const [params] = useSearchParams();
  const [source, setSource] = useState<"sample" | "upload">("sample"),
    [sampleId, setSampleId] = useState(
      () =>
        labSamples.find((s) => s.id === params.get("sample"))?.id ??
        labSamples[0].id,
    ),
    [sheetId, setSheetId] = useState("sheet_flag");
  const sample = labSamples.find((s) => s.id === sampleId)!;
  const sheets =
    capture.manifest?.records.filter((r) => r.kind === "verification") ?? [];
  const sheet = sheets.find((r) => r.id === sheetId) ?? sheets[0];
  const [file, setFile] = useState<File | null>(null),
    [written, setWritten] = useState<File | null>(null);
  const preview = usePreview(file),
    writtenPreview = usePreview(written);
  const [fieldType, setFieldType] = useState<"numeric" | "written">("numeric"),
    [mode, setMode] = useState<"baseline" | "proposed" | "both">("both");
  const [busy, setBusy] = useState(false),
    [elapsed, setElapsed] = useState(0),
    [step, setStep] = useState("");
  const [error, setError] = useState(""),
    [fresh, setFresh] = useState<
      Partial<Record<"baseline" | "proposed", FieldResult>>
    >({}),
    [verification, setVerification] = useState<VerifyResult | null>(null),
    [completed, setCompleted] = useState(false);
  const controller = useRef<AbortController | null>(null),
    running = useRef(false),
    output = useRef<HTMLElement>(null);
  const image =
    source === "upload"
      ? preview
      : kind === "recognition"
        ? sample.image
        : sheet?.image;
  const live = completed || Object.keys(fresh).length > 0;
  const responses =
    source === "sample" && !live && !busy
      ? {
          baseline: sample.responses.baseline.result,
          proposed: sample.responses.proposed.result,
        }
      : fresh;
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    if (!busy) return;
    const start = Date.now();
    const timer = setInterval(
      () => setElapsed(Math.floor((Date.now() - start) / 1000)),
      500,
    );
    return () => clearInterval(timer);
  }, [busy]);
  function reset() {
    setFresh({});
    setVerification(null);
    setCompleted(false);
    setError("");
  }
  function chooseFile(value: File, word = false) {
    const message = validateUpload(value);
    if (message) {
      setError(message);
      return;
    }
    reset();
    if (word) setWritten(value);
    else setFile(value);
  }
  async function savedFile(
    record: Pick<CaptureRecord, "image">,
    signal: AbortSignal,
  ) {
    const response = await fetch(record.image!, { signal });
    if (!response.ok) throw new Error("Sample image is unavailable.");
    const blob = await response.blob();
    return new File([blob], record.image!.split("/").pop()!, {
      type: blob.type || "image/png",
    });
  }
  async function run() {
    if (running.current || system.readiness !== "ready") return;
    if (
      source === "upload" &&
      (!file || (kind === "verification" && !written))
    ) {
      setError(
        kind === "verification"
          ? "Choose both a figures crop and a words crop."
          : "Choose a field crop first.",
      );
      return;
    }
    if (source === "sample" && kind === "verification" && !sheet) {
      setError("The saved input is still loading.");
      return;
    }
    running.current = true;
    const c = new AbortController();
    controller.current = c;
    reset();
    setBusy(true);
    setElapsed(0);
    try {
      if (kind === "recognition") {
        const input =
          source === "upload" ? file! : await savedFile(sample, c.signal);
        for (const next of mode === "both"
          ? (["baseline", "proposed"] as const)
          : [mode]) {
          setStep(
            next === "baseline" ? "Reading with baseline" : "Reading with ATHN",
          );
          const body = new FormData();
          body.append("image", input);
          body.append("mode", next);
          body.append(
            "field_type",
            source === "sample" ? sample.field_type : fieldType,
          );
          const result = await api.recognize(body, c.signal);
          if (c.signal.aborted) return;
          setFresh((old) => ({ ...old, [next]: result }));
          recordRun(
            "recognition",
            source === "sample" ? sample.title : input.name,
            result,
          );
        }
      } else {
        setStep("Reading figures, then words");
        const body = new FormData();
        body.append("mode", mode === "both" ? "baseline" : mode);
        if (source === "sample") {
          body.append("cheque_image", await savedFile(sheet, c.signal));
          body.append("numeric_roi", sheet.fields!.numeric_roi);
          body.append("written_roi", sheet.fields!.written_roi);
        } else {
          body.append("numeric_image", file!);
          body.append("written_image", written!);
        }
        const result = await api.verify(body, c.signal);
        if (c.signal.aborted) return;
        setVerification(result);
        recordRun(
          "verification",
          source === "sample"
            ? (sheet.description ?? sheet.id)
            : `${file!.name} + ${written!.name}`,
          result,
        );
      }
      setCompleted(true);
      requestAnimationFrame(() => {
        output.current?.focus({ preventScroll: true });
        if (matchMedia("(max-width: 1050px)").matches)
          output.current?.scrollIntoView({
            behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
              ? "instant"
              : "smooth",
            block: "start",
          });
      });
    } catch (e) {
      if (c.signal.aborted)
        setError(
          "Stopped waiting. An already-running model request may continue on the server.",
        );
      else
        setError(
          e instanceof ApiError
            ? `${e.message}${e.requestId ? ` · Request ${e.requestId}` : ""}`
            : e instanceof Error
              ? e.message
              : "The request failed.",
        );
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  return (
    <div className="live-lab">
      <header className="lab-heading">
        <div>
          <p className="eyebrow">LIVE MODEL / YOUR EVIDENCE</p>
          <h1>
            {kind === "recognition"
              ? "Look closer. Test a field."
              : "Two fields. One comparison."}
          </h1>
          <p>
            {kind === "recognition"
              ? "Choose an input. Compare the actual readings, preparation and parsed values."
              : "Provide the figures and the words. See where the recognised values agree, differ or need review."}
          </p>
        </div>
        <span className={`readiness-pill ${system.readiness}`}>
          {system.readiness === "ready" ? "Model connected" : "Model not ready"}
        </span>
      </header>
      <div className="lab-grid">
        <section className="lab-input polish-card">
          <div className="panel-heading">
            <h2>01 / Input evidence</h2>
            <span>
              {source === "sample" ? "DEV sample" : "Your field crops"}
            </span>
          </div>
          <div className="segmented" role="group" aria-label="Input source">
            {(["sample", "upload"] as const).map((v) => (
              <button
                key={v}
                aria-pressed={source === v}
                disabled={busy}
                onClick={() => {
                  setSource(v);
                  reset();
                }}
              >
                {v === "sample" ? "Sample library" : "Upload crops"}
              </button>
            ))}
          </div>
          {source === "sample" ? (
            kind === "recognition" ? (
              <div
                className="sample-strip"
                role="group"
                aria-label="Development sample library"
              >
                {labSamples.map((s) => (
                  <button
                    key={s.id}
                    aria-pressed={s.id === sample.id}
                    disabled={busy}
                    onClick={() => {
                      setSampleId(s.id);
                      reset();
                      setMode(s.field_type === "written" ? "baseline" : "both");
                    }}
                  >
                    <img src={s.image} alt="" />
                    <span>{s.title}</span>
                    <small>
                      {s.synthetic ? "Synthetic" : "Handwritten"} · DEV
                    </small>
                  </button>
                ))}
              </div>
            ) : (
              <label className="lab-select">
                Recorded comparison
                <select
                  aria-label="Verification sample"
                  value={sheet?.id ?? ""}
                  disabled={busy}
                  onChange={(e) => {
                    setSheetId(e.target.value);
                    reset();
                  }}
                >
                  {sheets.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id === "sheet_flag"
                        ? "Different amounts / 25000 vs written field"
                        : s.id === "sheet_accept"
                          ? "Matching amounts / genuine handwriting"
                          : "Unresolved words / synthetic input"}
                    </option>
                  ))}
                </select>
              </label>
            )
          ) : (
            <div className="lab-uploads">
              <UploadField
                label={
                  kind === "recognition"
                    ? "Choose a field crop"
                    : "Choose the figures crop"
                }
                file={file}
                onFile={(f) => chooseFile(f)}
                disabled={busy}
              />
              {kind === "verification" && (
                <UploadField
                  label="Choose the words crop"
                  file={written}
                  onFile={(f) => chooseFile(f, true)}
                  disabled={busy}
                />
              )}
            </div>
          )}
          <div
            className={`lab-preview${kind === "verification" && source === "upload" ? " paired" : ""}`}
          >
            {image ? (
              <img src={image} alt="Selected input pixels for live inference" />
            ) : (
              <div className="lab-empty">
                <UploadCloud size={36} />
                <span>Your original pixels appear here.</span>
              </div>
            )}
            {kind === "verification" &&
              source === "upload" &&
              writtenPreview && (
                <img
                  src={writtenPreview}
                  alt="Selected written amount pixels"
                />
              )}
            <span className="preview-cross top-left" />
            <span className="preview-cross bottom-right" />
          </div>
          <div className="lab-input-meta">
            <span>
              {source === "sample"
                ? kind === "recognition"
                  ? `${sample.synthetic ? "Synthetic" : "Genuine handwriting"} · ${sample.field_type} · DEV`
                  : "Constructed DEV pair"
                : "Original upload · not added to the sample library"}
            </span>
            <span>Original pixels retained</span>
          </div>
          <div className="lab-settings">
            {kind === "recognition" && (
              <label>
                Field type
                <select
                  aria-label="Field type"
                  value={source === "sample" ? sample.field_type : fieldType}
                  disabled={busy || source === "sample"}
                  onChange={(e) => {
                    setFieldType(e.target.value as typeof fieldType);
                    reset();
                  }}
                >
                  <option value="numeric">Figures / numeric</option>
                  <option value="written">Words / English amount</option>
                </select>
              </label>
            )}
            <label>
              Preparation
              <select
                aria-label="Recognition preparation"
                value={
                  kind === "verification" && mode === "both" ? "baseline" : mode
                }
                disabled={busy}
                onChange={(e) => {
                  setMode(e.target.value as typeof mode);
                  reset();
                }}
              >
                {kind === "recognition" && (
                  <option value="both">Compare both methods</option>
                )}
                <option value="baseline">Baseline</option>
                <option value="proposed">ATHN</option>
              </select>
            </label>
          </div>
          <p className="lab-help">
            Use synthetic or consented crops.{" "}
            {kind === "recognition"
              ? "One amount field per image. Paired calls run sequentially."
              : "Two separate crops, selected by you; no automatic field detection."}
          </p>
          <div className="lab-run-actions">
            <button
              className="button primary"
              onClick={() => void run()}
              disabled={busy || system.readiness !== "ready"}
            >
              <Play size={16} />
              {busy
                ? `${step} · ${elapsed}s`
                : kind === "recognition"
                  ? "Run recognition"
                  : "Compare amounts"}
            </button>
            {busy && (
              <button
                className="button secondary"
                onClick={() => controller.current?.abort()}
              >
                <Square size={13} /> Stop waiting
              </button>
            )}
          </div>
          {busy && (
            <p className="lab-progress" role="status">
              {step} · {elapsed} seconds elapsed
            </p>
          )}
          {error && (
            <div className="error-list" role="alert">
              {error}
            </div>
          )}
        </section>
        <section
          className="lab-output polish-card"
          ref={output}
          tabIndex={-1}
          aria-label="Model result"
          aria-live="polite"
        >
          <div className="panel-heading">
            <h2>02 / Read the result</h2>
            <span className={`capture-chip ${live ? "fresh" : ""}`}>
              {live
                ? "Live API response"
                : source === "sample" && kind === "recognition" && !busy
                  ? "Recorded API response"
                  : "Waiting for your run"}
            </span>
          </div>
          {kind === "recognition" ? (
            Object.keys(responses).length ? (
              <>
                <div className="lab-response-grid">
                  {(["baseline", "proposed"] as const).map(
                    (m) =>
                      responses[m] && (
                        <FieldResultCard
                          key={m}
                          title={m === "baseline" ? "Baseline" : "With ATHN"}
                          result={responses[m]!}
                          compact
                        />
                      ),
                  )}
                </div>
                <div className="lab-readout-note">
                  <ArrowRight size={18} />
                  <p>
                    The model's raw reading stays visible. A null parsed value
                    remains unresolved.
                  </p>
                </div>
                <ResultDownload
                  value={{
                    source: live ? "live" : "saved",
                    sample: source === "sample" ? sample.source_id : undefined,
                    responses,
                  }}
                />
              </>
            ) : (
              <div className="lab-output-empty">
                <span className="empty-equals">
                  Aa <ArrowRight size={22} /> 0.00
                </span>
                <h3>A reading, with its evidence.</h3>
                <p>
                  Run the model to see the raw text, strict parsed value and
                  measured response time here.
                </p>
              </div>
            )
          ) : verification ? (
            <>
              <div className={`lab-decision ${verification.decision}`}>
                <span>
                  {verification.decision === "accept"
                    ? "="
                    : verification.decision === "flag"
                      ? "≠"
                      : "?"}
                </span>
                <h3>
                  {verification.decision === "accept"
                    ? "Amounts agree"
                    : verification.decision === "flag"
                      ? "Amounts differ"
                      : "Needs human review"}
                </h3>
                {verification.reasons.map((r) => (
                  <p key={r}>{r}</p>
                ))}
              </div>
              <div className="lab-response-grid">
                <FieldResultCard
                  title="Amount in figures"
                  result={verification.numeric}
                  compact
                />
                <FieldResultCard
                  title="Amount in words"
                  result={verification.written}
                  compact
                />
              </div>
              <p className="lab-help">{verification.notice}</p>
              <ResultDownload value={verification} />
            </>
          ) : (
            <div className="lab-output-empty">
              <span className="empty-equals">
                00 <ArrowRight size={22} /> Aa
              </span>
              <h3>Agreement needs both readings.</h3>
              <p>
                The comparison stays open until each field has been read and
                parsed.
              </p>
            </div>
          )}
          <div className="lab-output-foot">
            <span>Frozen LoGo-HTR</span>
            <span>No spelling repair. No hidden correction.</span>
          </div>
        </section>
      </div>
    </div>
  );
}
