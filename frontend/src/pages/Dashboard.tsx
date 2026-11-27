import { useOutletContext, Link } from "react-router-dom";
import {
  RefreshCw,
  Cpu,
  Fingerprint,
  CircleCheck,
  CircleAlert,
  CircleHelp,
  ScanLine,
  TextSearch,
  ChartNoAxesCombined,
  BookOpen,
  Layers,
} from "lucide-react";
import { API_BASE_URL } from "../api/client";
import type { useModelStatus } from "../hooks/useModelStatus";
import { useCaptureContext } from "../hooks/useSavedCapture";

const labels = {
  loading: "Checking system",
  ready: "Model ready",
  unavailable: "Model not loaded",
  offline: "Backend unreachable",
  error: "Unexpected API error",
};
const workspaces = [
  {
    to: "/verify",
    title: "Cheque verification",
    description:
      "Inspect three captured comparisons and rerun the original examples.",
    milestone: "F2",
    icon: ScanLine,
  },
  {
    to: "/recognize",
    title: "Amount recognition",
    description:
      "Inspect the handwriting in one field and the text produced by the model.",
    milestone: "F3",
    icon: TextSearch,
  },
  {
    to: "/benchmarks",
    title: "Research benchmarks",
    description:
      "Compare baseline and ATHN results across genuine and synthetic data.",
    milestone: "F4",
    icon: ChartNoAxesCombined,
  },
];
export function Dashboard() {
  const s = useOutletContext<ReturnType<typeof useModelStatus>>();
  const capture = useCaptureContext();
  const info = s.info;
  const Icon =
    s.readiness === "ready"
      ? CircleCheck
      : s.readiness === "loading"
        ? CircleHelp
        : CircleAlert;
  return (
    <div className="dashboard-redesign">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">CHEQUEVERIFY / RESEARCH WORKSPACE</p>
          <h1>Your work, in focus.</h1>
          <p>
            Inspect handwriting, compare amounts, and understand the evidence
            behind each result.
          </p>
        </div>
        <Link className="field-notes-shortcut" to="/">
          <BookOpen size={20} aria-hidden="true" />
          Project introduction
        </Link>
      </div>
      {capture.manifest && (
        <section className="saved-run-banner">
          <div>
            <span className="capture-chip">ACTUAL API RESULTS SAVED</span>
            <h2>A real backend run, ready to inspect.</h2>
            <p>
              {capture.manifest.records.length} responses captured ·{" "}
              {capture.manifest.captured_at} (UTC)
            </p>
            <p>
              Constructed DEV demos and short field crops, plus the existing
              saved research benchmark. No new accuracy evaluation.
            </p>
          </div>
          <Link className="button primary" to="/verify">
            Inspect captured results
          </Link>
        </section>
      )}
      <section
        className={`system-status ${s.readiness}`}
        aria-label="System status"
      >
        <div role="status" aria-live="polite">
          <Icon size={26} aria-hidden="true" />
          <div>
            <h2>{labels[s.readiness]}</h2>
            <p>
              {s.readiness === "ready"
                ? "The backend is connected. LoGo-HTR is loaded for CPU inference."
                : s.readiness === "loading"
                  ? "Reading the backend health and model information."
                  : s.readiness === "unavailable"
                    ? "The backend is reachable. Recognition is unavailable until the model is loaded."
                    : s.readiness === "offline"
                      ? "Start the backend server, then check the connection again."
                      : "The API returned an unexpected response. See the details below."}
            </p>
          </div>
        </div>
        <div className="status-actions">
          <code>{API_BASE_URL}</code>
          <button
            className="button secondary"
            disabled={s.loading}
            onClick={() => void s.refresh()}
          >
            <RefreshCw
              size={18}
              className={s.loading ? "spin" : ""}
              aria-hidden="true"
            />
            Check again
          </button>
        </div>
      </section>
      {s.errors.length > 0 && (
        <div className="error-list" role="alert">
          {s.errors.map((e, i) => (
            <div key={i}>
              <p>{e.message}</p>
              <small>
                {e.status && `HTTP ${e.status}`}
                {e.code && ` · ${e.code}`}
                {e.requestId && ` · Request ${e.requestId}`}
              </small>
            </div>
          ))}
        </div>
      )}
      <section className="workspace-tools" aria-labelledby="tools-title">
        <div className="workspace-section-heading">
          <h2 id="tools-title">Choose a workspace</h2>
          <p>Actual saved responses and manual backend reruns</p>
        </div>
        <div className="tool-grid">
          {workspaces.map(
            ({ to, title, description, milestone, icon: ToolIcon }) => (
              <Link className="workspace-tool" to={to} key={to}>
                <div className="tool-top">
                  <span className="tool-icon">
                    <ToolIcon size={26} strokeWidth={1.5} aria-hidden="true" />
                  </span>
                  <span className="pending-tag">
                    {capture.loading
                      ? `Loading ${milestone}`
                      : capture.manifest
                        ? "Results available"
                        : "Capture unavailable"}
                  </span>
                </div>
                <h3>{title}</h3>
                <p>{description}</p>
                <span className="tool-footer">Open results workspace</span>
              </Link>
            ),
          )}
        </div>
      </section>
      <section
        className="engine-section"
        aria-label="Model and recognition methods"
      >
        <article className="engine-card">
          <div className="engine-card-top">
            <p className="eyebrow">THE RECOGNITION ENGINE</p>
            <Cpu size={24} strokeWidth={1.5} aria-hidden="true" />
          </div>
          <h2>{info ? "LoGo-HTR" : "Model information"}</h2>
          <p className="engine-description">
            {info?.model ??
              "Model information will appear when the API responds."}
          </p>
          <dl className="engine-metrics">
            <div>
              <dt>Parameters</dt>
              <dd>
                {info?.parameter_count != null
                  ? info.parameter_count.toLocaleString("en-US")
                  : "Not available"}
              </dd>
            </div>
            <div>
              <dt>Device</dt>
              <dd>{info?.device ?? "Not available"}</dd>
            </div>
            <div>
              <dt>Default mode</dt>
              <dd>{info?.default_mode ?? "Not available"}</dd>
            </div>
          </dl>
          <div className="engine-footnote">
            <Fingerprint size={20} aria-hidden="true" />
            <span>Frozen checkpoint · inference only</span>
          </div>
        </article>
        <article className="method-card">
          <div className="workspace-section-heading">
            <h2>One model. Two methods.</h2>
            <Layers size={22} strokeWidth={1.5} aria-hidden="true" />
          </div>
          <p className="method-intro">
            The same recogniser, with a different preparation step.
          </p>
          <div className="method-option">
            <div className="method-label">
              <span>BASELINE</span>
              {info?.default_mode === "baseline" && (
                <span className="default-tag">Default</span>
              )}
            </div>
            <h3>Original pipeline</h3>
            <p>{info?.modes.baseline ?? "Awaiting model information."}</p>
          </div>
          <div className="method-option proposed-option">
            <div className="method-label">
              <span>PROPOSED / ATHN</span>
              {info?.default_mode === "proposed" && (
                <span className="default-tag">Default</span>
              )}
            </div>
            <h3>Adaptive text-height normalisation</h3>
            <p>
              {info?.modes.proposed.method ?? "Awaiting model information."}
            </p>
            {info && (
              <div className="method-config">
                <span>
                  Config{" "}
                  <strong>
                    {info.modes.proposed.config?.id ?? "Not available"}
                  </strong>
                </span>
                <span>
                  Status{" "}
                  <strong>
                    {info.modes.proposed.status ?? "Not available"}
                  </strong>
                </span>
              </div>
            )}
          </div>
        </article>
      </section>
      <section className="research-boundaries">
        <div className="workspace-section-heading">
          <div>
            <p className="eyebrow">READ BEFORE USING</p>
            <h2>Keep the result in context.</h2>
          </div>
          <span className="review-label">Human review required</span>
        </div>
        {info ? (
          <ul>
            {info.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        ) : (
          <p>
            Model limitations have not been retrieved. Check the connection
            before using recognition.
          </p>
        )}
      </section>
      {info && (
        <details className="technical">
          <summary>
            <span>Model provenance & pipeline</span>
            <span className="technical-hint">
              Checkpoint, dictionary and decoding
            </span>
          </summary>
          <dl>
            <dt>Checkpoint SHA-256</dt>
            <dd>
              <code>{info.checkpoint_sha256}</code>
            </dd>
            <dt>Upstream commit</dt>
            <dd>
              <code>{info.upstream_commit}</code>
            </dd>
            <dt>Dictionary</dt>
            <dd>{info.dictionary}</dd>
            <dt>Preprocessing</dt>
            <dd>{info.preprocessing}</dd>
            <dt>Decoding</dt>
            <dd>{info.decoding}</dd>
          </dl>
        </details>
      )}
    </div>
  );
}
