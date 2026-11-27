import { useOutletContext, Link } from "react-router-dom";
import {
  RefreshCw,
  Cpu,
  Fingerprint,
  Layers,
  CircleCheck,
  CircleAlert,
  CircleHelp,
} from "lucide-react";
import { API_BASE_URL } from "../api/client";
import type { useModelStatus } from "../hooks/useModelStatus";

const labels = {
  loading: "Checking system",
  ready: "Model ready",
  unavailable: "Model not loaded",
  offline: "Backend unreachable",
  error: "Unexpected API error",
};
export function Dashboard() {
  const s = useOutletContext<ReturnType<typeof useModelStatus>>();
  const info = s.info;
  const Icon =
    s.readiness === "ready"
      ? CircleCheck
      : s.readiness === "loading"
        ? CircleHelp
        : CircleAlert;
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">SYSTEM OVERVIEW</p>
          <h1>A clear view of the model.</h1>
          <p>
            Read handwritten amounts. Compare their values. Keep a person in the
            loop.
          </p>
        </div>
        <button
          className="button secondary"
          disabled={s.loading}
          onClick={() => void s.refresh()}
        >
          <RefreshCw
            size={16}
            className={s.loading ? "spin" : ""}
            aria-hidden="true"
          />
          Check again
        </button>
      </div>
      <section
        className={`system-status ${s.readiness}`}
        aria-label="System status"
      >
        <div role="status" aria-live="polite">
          <Icon size={22} aria-hidden="true" />
          <div>
            <h2>{labels[s.readiness]}</h2>
            <p>
              {s.readiness === "ready"
                ? "The backend is reachable and the recognition model is loaded."
                : s.readiness === "loading"
                  ? "Contacting the backend and reading model information."
                  : s.readiness === "unavailable"
                    ? "The backend is reachable. Recognition is unavailable until the model is loaded."
                    : s.readiness === "offline"
                      ? "Check the backend server and connection, then try again."
                      : "The API returned an unexpected response. Check the details below."}
            </p>
          </div>
        </div>
        <code>{API_BASE_URL}</code>
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
      <div className="overview-grid">
        <section className="model-panel">
          <div className="panel-heading">
            <span className="eyebrow">RECOGNITION ENGINE</span>
            <Cpu size={20} aria-hidden="true" />
          </div>
          <h2>{info ? "LoGo-HTR" : "Model information"}</h2>
          <p>
            {info?.model ?? "Model details will appear when the API responds."}
          </p>
          <dl className="engine-facts">
            <div>
              <dt>Parameters</dt>
              <dd>
                {info?.parameter_count != null
                  ? info.parameter_count.toLocaleString("en-US")
                  : "Not available"}
              </dd>
            </div>
            <div>
              <dt>Inference device</dt>
              <dd>{info?.device ?? "Not available"}</dd>
            </div>
            <div>
              <dt>Default mode</dt>
              <dd>{info?.default_mode ?? "Not available"}</dd>
            </div>
          </dl>
          <div className="model-rule" />
          <div className="model-note">
            <Fingerprint size={18} aria-hidden="true" />
            <span>Frozen checkpoint. Inference only.</span>
          </div>
        </section>
        <section className="modes-panel">
          <div className="section-title">
            <h2>Two paths. One recogniser.</h2>
            <Layers size={19} aria-hidden="true" />
          </div>
          <p className="section-intro">
            The proposed method adds preprocessing to the unchanged model.
          </p>
          <article className="mode-row">
            <div>
              <span className="mode-tag">BASELINE</span>
              {info?.default_mode === "baseline" && (
                <span className="default-tag">Default</span>
              )}
            </div>
            <h3>Original model pipeline</h3>
            <p>{info?.modes.baseline ?? "Awaiting model information."}</p>
          </article>
          <article className="mode-row">
            <div>
              <span className="mode-tag">PROPOSED / ATHN</span>
              {info?.default_mode === "proposed" && (
                <span className="default-tag">Default</span>
              )}
            </div>
            <h3>Adaptive text-height normalisation</h3>
            <p>
              {info?.modes.proposed.method ?? "Awaiting model information."}
            </p>
            {info && (
              <p className="config-line">
                Config: {info.modes.proposed.config?.id ?? "Not available"} ·
                Status: {info.modes.proposed.status ?? "Not available"}
              </p>
            )}
          </article>
        </section>
      </div>
      <section className="next-section">
        <div>
          <p className="eyebrow">APPLICATION WORKFLOW</p>
          <h2>From handwriting to a comparison.</h2>
        </div>
        <div className="workflow-links">
          <Link to="/verify">
            <span className="workflow-number">01</span>
            <strong>Mark the amount fields</strong>
            <span>Cheque verification · Pending F2</span>
          </Link>
          <Link to="/recognize">
            <span className="workflow-number">02</span>
            <strong>Inspect recognised text</strong>
            <span>Amount recognition · Pending F3</span>
          </Link>
          <Link to="/benchmarks">
            <span className="workflow-number">03</span>
            <strong>Explore the evidence</strong>
            <span>Research benchmarks · Pending F4</span>
          </Link>
        </div>
      </section>
      <section className="limitations">
        <div>
          <span className="eyebrow">READ BEFORE USING</span>
          <h2>What this system can tell you.</h2>
        </div>
        {info ? (
          <ul>
            {info.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        ) : (
          <p>
            Model limitations could not yet be retrieved. Check the connection
            before using recognition.
          </p>
        )}
      </section>
      {info && (
        <details className="technical">
          <summary>Checkpoint & pipeline details</summary>
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
    </>
  );
}
