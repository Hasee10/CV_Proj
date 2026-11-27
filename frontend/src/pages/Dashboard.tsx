import { useOutletContext, Link } from "react-router-dom";
import {
  RefreshCw,
  ScanLine,
  TextSearch,
  ChartNoAxesCombined,
  Cpu,
  ArrowUpRight,
} from "lucide-react";
import { API_BASE_URL } from "../api/client";
import type { useModelStatus } from "../hooks/useModelStatus";
import type { BenchmarkResult } from "../api/results";
import { formatJson, useCaptureContext } from "../hooks/useSavedCapture";
import { ResearchHighlights } from "../components/research/BenchmarkVisuals";

const labels = {
  loading: "Checking model",
  ready: "Model ready",
  unavailable: "Model not loaded",
  offline: "Backend offline",
  error: "Connection error",
};
const workspaces = [
  {
    to: "/verify",
    title: "Cheque verification",
    text: "Inspect two amount fields and their comparison.",
    icon: ScanLine,
    action: "Open verification",
  },
  {
    to: "/recognize",
    title: "Amount recognition",
    text: "Compare baseline and ATHN on the same input.",
    icon: TextSearch,
    action: "Inspect recognition",
  },
  {
    to: "/benchmarks",
    title: "Research benchmarks",
    text: "Explore the frozen results and their limits.",
    icon: ChartNoAxesCombined,
    action: "Explore benchmarks",
  },
];
export function Dashboard() {
  const system = useOutletContext<ReturnType<typeof useModelStatus>>();
  const capture = useCaptureContext();
  const info = system.info;
  const benchmark = capture.responses.benchmark as BenchmarkResult | undefined;
  return (
    <div className="dashboard-polish">
      <header className="polish-page-heading">
        <div>
          <p className="eyebrow">CHEQUEVERIFY / RESEARCH WORKSPACE</p>
          <h1>Cheque verification workspace</h1>
          <p>Inspect handwriting, compare values, and explore the evidence.</p>
        </div>
        <span className={`readiness-pill ${system.readiness}`}>
          {labels[system.readiness]}
        </span>
      </header>
      <div className="dashboard-overview">
        <section className="workspace-welcome polish-card">
          <div>
            <p className="eyebrow">START AN INSPECTION</p>
            <h2>
              From handwriting
              <br />
              to an amount decision.
            </h2>
            <p>
              Open a recorded example, inspect both fields, and rerun it through
              the real model.
            </p>
            <Link className="button primary" to="/verify">
              Open verification <ArrowUpRight size={17} aria-hidden="true" />
            </Link>
          </div>
          <figure className="concept-cheque">
            <figcaption>Illustrative workflow</figcaption>
            <svg
              viewBox="0 0 240 175"
              role="img"
              aria-label="Explanatory cheque-field illustration: words and figures represent one amount"
            >
              <rect
                x="1"
                y="1"
                width="238"
                height="173"
                rx="7"
                fill="#fbfcf7"
                stroke="#bacbb7"
              />
              <text x="16" y="25" className="concept-caption">
                Amount in words
              </text>
              <rect
                x="15"
                y="34"
                width="210"
                height="48"
                rx="4"
                fill="white"
                stroke="#72579c"
                strokeDasharray="3 3"
              />
              <text x="28" y="65" className="concept-ink">
                one
              </text>
              <text x="16" y="104" className="concept-caption">
                Amount in figures
              </text>
              <rect
                x="15"
                y="112"
                width="210"
                height="48"
                rx="4"
                fill="white"
                stroke="#28685c"
                strokeDasharray="3 3"
              />
              <text x="28" y="145" className="concept-ink">
                1.00
              </text>
            </svg>
          </figure>
        </section>
        <section className="polish-card engine-overview">
          <div className="panel-heading">
            <h2>Recognition engine</h2>
            <Cpu size={20} aria-hidden="true" />
          </div>
          <strong className="engine-name">LoGo-HTR</strong>
          <p>Official frozen checkpoint · CPU inference</p>
          <dl className="engine-summary">
            <div>
              <dt>Parameters</dt>
              <dd>
                {info?.parameter_count != null
                  ? info.parameter_count.toLocaleString("en-US")
                  : "Unavailable"}
              </dd>
            </div>
            <div>
              <dt>Methods</dt>
              <dd>Baseline + ATHN</dd>
            </div>
          </dl>
          <div className="engine-status">
            <span className={`readiness-pill ${system.readiness}`}>
              {labels[system.readiness]}
            </span>
            <button
              className="button secondary"
              disabled={system.loading}
              onClick={() => void system.refresh()}
            >
              <RefreshCw size={15} aria-hidden="true" />
              Check again
            </button>
          </div>
          <details className="technical">
            <summary>Model provenance &amp; limitations</summary>
            <p>{API_BASE_URL}</p>
            <pre>
              {info
                ? formatJson(info)
                : "Live model information is unavailable. Saved results remain accessible."}
            </pre>
          </details>
        </section>
      </div>
      {system.errors.length > 0 && (
        <div className="error-list" role="alert">
          {system.errors.map((e, i) => (
            <p key={i}>
              {e.message}
              {e.code && ` · ${e.code}`}
              {e.requestId && ` · ${e.requestId}`}
            </p>
          ))}
        </div>
      )}
      <nav className="workspace-entry-grid" aria-label="Choose a workspace">
        {workspaces.map(({ to, title, text, icon: Icon, action }) => (
          <Link className="polish-card workspace-entry" key={to} to={to}>
            <span className="entry-icon">
              <Icon size={23} aria-hidden="true" />
            </span>
            <h2>{title}</h2>
            <p>{text}</p>
            <span className="entry-action">
              {action}
              <ArrowUpRight size={17} aria-hidden="true" />
            </span>
          </Link>
        ))}
      </nav>
      <section className="dashboard-research">
        <div className="panel-heading">
          <h2>Evidence at a glance</h2>
          <span>Frozen historical research</span>
        </div>
        {benchmark ? (
          <ResearchHighlights data={benchmark} />
        ) : (
          <p role="status">{capture.error ?? "Loading recorded research…"}</p>
        )}
      </section>
      <p className="dashboard-context">
        Recognition compares values; it does not establish cheque authenticity.
        No real handwritten cheques were evaluated. Saved examples remain
        available when the backend is offline.
      </p>
    </div>
  );
}
