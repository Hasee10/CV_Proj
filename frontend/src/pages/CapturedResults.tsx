import { useEffect, useRef, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { Play, Equal, CircleAlert, SquarePen } from "lucide-react";
import { api, ApiError } from "../api/client";
import type { FieldResult, VerifyResult } from "../api/results";
import type { useModelStatus } from "../hooks/useModelStatus";
import { useCaptureContext } from "../hooks/useSavedCapture";
import {
  CaptureProvenance,
  FieldResultCard,
} from "../components/results/ResultDetails";
import { EvidencePanel } from "../components/results/EvidencePanel";
import { LiveLab } from "../components/results/LiveLab";
import { recordRun } from "../lib/sessionRuns";
import {
  RecognitionComparison,
  RecognitionPipeline,
} from "../components/results/RecognitionComparison";
const decisionLabels = {
  accept: "Amounts agree",
  flag: "Amounts differ",
  review: "Needs human review",
};
const exampleLabels: Record<string, string> = {
  sheet_accept: "Agreement example",
  sheet_flag: "Mismatch example",
  sheet_review: "Review example",
  "numeric-baseline": "Synthetic numeric · baseline",
  "numeric-proposed": "Synthetic numeric · ATHN",
  "written-baseline": "Handwritten word · baseline",
};
export function CapturedResults({
  kind,
}: {
  kind: "verification" | "recognition";
}) {
  const [params] = useSearchParams();
  const [view, setView] = useState<"live" | "saved">(() =>
    params.has("example") ? "saved" : "live",
  );
  return (
    <div className="workspace-lab-page">
      <div
        className="workspace-view-tabs"
        role="group"
        aria-label="Workspace view"
      >
        <button aria-pressed={view === "live"} onClick={() => setView("live")}>
          Live lab
        </button>
        <button
          aria-pressed={view === "saved"}
          onClick={() => setView("saved")}
        >
          Archived comparisons
        </button>
      </div>
      {view === "live" ? (
        <LiveLab key={kind} kind={kind} />
      ) : (
        <SavedResults kind={kind} />
      )}
    </div>
  );
}
export function SavedResults({
  kind,
}: {
  kind: "verification" | "recognition";
}) {
  const capture = useCaptureContext();
  const system = useOutletContext<ReturnType<typeof useModelStatus>>();
  const records =
    capture.manifest?.records.filter((r) => r.kind === kind) ?? [];
  const [searchParams] = useSearchParams();
  const [selected, setSelected] = useState(
    () => searchParams.get("example") ?? "",
  );
  const record = records.find((r) => r.id === selected) ?? records[0];
  const [fresh, setFresh] = useState<{
    id: string;
    result: VerifyResult | FieldResult;
    at: string;
  } | null>(null);
  const [busy, setBusy] = useState(false),
    [elapsed, setElapsed] = useState(0),
    [error, setError] = useState<ApiError | null>(null);
  const active = useRef<AbortController | null>(null),
    running = useRef(false),
    resultHeading = useRef<HTMLHeadingElement>(null),
    errorSummary = useRef<HTMLDivElement>(null);
  useEffect(() => () => active.current?.abort(), []);
  useEffect(() => {
    if (!busy) return;
    const start = Date.now();
    const timer = setInterval(
      () => setElapsed(Math.floor((Date.now() - start) / 1000)),
      1000,
    );
    return () => clearInterval(timer);
  }, [busy]);
  const isFresh = Boolean(fresh && record && fresh.id === record.id);
  const result = (
    isFresh ? fresh?.result : capture.responses[record?.id ?? ""]
  ) as VerifyResult | FieldResult | undefined;
  async function rerun() {
    if (
      !record?.image ||
      !record.fields ||
      running.current ||
      system.readiness !== "ready"
    )
      return;
    running.current = true;
    const controller = new AbortController();
    active.current = controller;
    setBusy(true);
    setElapsed(0);
    setError(null);
    setFresh(null);
    try {
      const imageResponse = await fetch(record.image, {
        signal: controller.signal,
      });
      if (!imageResponse.ok)
        throw new Error("The saved input image is unavailable.");
      const blob = await imageResponse.blob();
      const body = new FormData();
      Object.entries(record.fields).forEach(([key, value]) =>
        body.append(key, value),
      );
      body.append(
        kind === "verification" ? "cheque_image" : "image",
        new File([blob], record.image.split("/").pop()!, {
          type: blob.type || "image/png",
        }),
      );
      const data =
        kind === "verification"
          ? await api.verify(body, controller.signal)
          : await api.recognize(body, controller.signal);
      if (!controller.signal.aborted) {
        setFresh({ id: record.id, result: data, at: new Date().toISOString() });
        recordRun(kind, record.description ?? record.id, data);
        requestAnimationFrame(() => resultHeading.current?.focus());
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        setError(
          e instanceof ApiError
            ? e
            : new ApiError(
                e instanceof Error ? e.message : "Request failed.",
                null,
              ),
        );
        if (e instanceof ApiError && e.code === "model_unavailable")
          void system.refresh();
        requestAnimationFrame(() => errorSummary.current?.focus());
      }
    } finally {
      running.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  if (capture.loading)
    return <p role="status">Loading captured backend results…</p>;
  if (capture.error || !capture.manifest || !record || !result)
    return (
      <div className="error-list" role="alert">
        {capture.error ??
          "No saved responses are available. Run the capture script to create them."}
      </div>
    );
  const verification =
    kind === "verification" ? (result as VerifyResult) : null;
  const icon =
    verification?.decision === "accept" ? (
      <Equal aria-hidden="true" />
    ) : verification?.decision === "flag" ? (
      <CircleAlert aria-hidden="true" />
    ) : (
      <SquarePen aria-hidden="true" />
    );
  return (
    <div className="captured-results">
      <header className="results-heading">
        <p className="eyebrow">ACTUAL BACKEND RESPONSES</p>
        <h1>
          {kind === "verification"
            ? "Cheque verification results"
            : "Amount recognition results"}
        </h1>
        <p>
          {kind === "verification"
            ? "Input evidence and recognised values, together. Three constructed DEV examples."
            : "One input, two recognition methods. Inspect the actual model output."}
        </p>
      </header>
      <div className="capture-source-banner">
        <span className="capture-chip">
          {isFresh ? "Fresh API response" : "Saved API capture"}
        </span>
        <span>{isFresh ? fresh?.at : capture.manifest.captured_at} (UTC)</span>
        <a href={record.response} download>
          Saved JSON
        </a>
      </div>
      <div className="result-toolbar">
        <label>
          Example
          <select
            value={record.id}
            disabled={busy}
            onChange={(e) => {
              setSelected(e.target.value);
              setError(null);
              setFresh(null);
            }}
          >
            {records.map((r) => (
              <option key={r.id} value={r.id}>
                {exampleLabels[r.id] ?? r.id}
              </option>
            ))}
          </select>
        </label>
        <button
          className="button primary"
          onClick={() => void rerun()}
          disabled={busy || system.readiness !== "ready"}
        >
          <Play size={17} aria-hidden="true" />
          {busy ? `Running · ${elapsed} s` : "Run this case again"}
        </button>
      </div>
      {system.readiness !== "ready" && (
        <p className="result-help">
          Fresh recognition is unavailable until the model is ready. Saved
          results remain available.
        </p>
      )}
      <p className="result-help">
        {record.synthetic
          ? "Synthetic font-rendered input."
          : "Genuine handwriting used in a constructed demonstration."}{" "}
        These examples are not real cheques or accuracy evidence.
      </p>
      {busy && (
        <p role="status" className="result-loading">
          {kind === "verification"
            ? "Recognising numeric then written amount"
            : "Recognising the selected field"}{" "}
          · {elapsed} seconds elapsed
        </p>
      )}
      {error && (
        <div
          role="alert"
          tabIndex={-1}
          ref={errorSummary}
          className="error-list"
        >
          <p>{error.message}</p>
          <p>
            {error.status && `HTTP ${error.status}`}
            {error.code && ` · ${error.code}`}
            {error.requestId && ` · Request ${error.requestId}`}
          </p>
          {error.code === "busy" && (
            <p>
              The server is processing another recognition. Retry manually in a
              moment.
            </p>
          )}
          {error.code === "inference_timeout" && (
            <p>
              The server may still be working and may remain busy. Retry
              manually later; baseline is recommended for written lines.
            </p>
          )}
          <p>The saved result below is from the earlier capture.</p>
        </div>
      )}
      <div className="inspection-workspace">
        <div className="inspection-evidence">
          <EvidencePanel
            key={record.id}
            record={record}
            rois={verification?.rois}
          />
          {kind === "recognition" && <RecognitionPipeline />}
        </div>
        <section className="inspection-result polish-card" aria-live="polite">
          {verification ? (
            <>
              <div className="panel-heading">
                <h2>Comparison result</h2>
                <span className="capture-chip">
                  {isFresh ? "Fresh live" : "Saved capture"}
                </span>
              </div>
              <div className={`decision-panel ${verification.decision}`}>
                <div>
                  {icon}
                  <h2 ref={resultHeading} tabIndex={-1}>
                    {decisionLabels[verification.decision]}
                  </h2>
                </div>
                <ul>
                  {verification.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
              <div className="field-results-grid">
                <FieldResultCard
                  compact
                  title="Amount in figures"
                  result={verification.numeric}
                />
                <FieldResultCard
                  compact
                  title="Amount in words"
                  result={verification.written}
                />
              </div>
              <div className="inspection-facts">
                <span>
                  Total inference time{" "}
                  <strong>
                    {String(verification.total_latency_seconds)} s
                  </strong>
                </span>
                <span>
                  Mode <strong>{verification.mode}</strong>
                </span>
              </div>
              <p className="authenticity-notice">{verification.notice}</p>
            </>
          ) : (
            <>
              <h2 className="sr-only" ref={resultHeading} tabIndex={-1}>
                Recognition result
              </h2>
              <RecognitionComparison
                capture={capture}
                record={record}
                current={result as FieldResult}
                fresh={isFresh}
              />
            </>
          )}
          <details className="request-details">
            <summary>Request details &amp; original JSON</summary>
            <p>
              Request{" "}
              {verification?.request_id ?? (result as FieldResult).request_id}
            </p>
            {verification?.rois && (
              <pre>{JSON.stringify(verification.rois, null, 2)}</pre>
            )}
            <p>The saved JSON download retains the original disk capture.</p>
          </details>
        </section>
      </div>
      {isFresh && (
        <p className="result-help">
          This fresh response is held in memory only. The original saved capture
          remains on disk; run the capture command to retain another complete
          run.
        </p>
      )}
      <details className="session-details">
        <summary>Request behaviour</summary>
        <p>
          Leaving this page stops waiting in the browser; an already-running
          model call can continue on the server. No requests are retried
          automatically.
        </p>
      </details>
      <CaptureProvenance record={record} manifest={capture.manifest} />
    </div>
  );
}
