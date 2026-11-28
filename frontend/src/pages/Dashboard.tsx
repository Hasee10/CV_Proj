import { useOutletContext, Link } from "react-router-dom";
import {
  ArrowUpRight,
  Cpu,
  RefreshCw,
  ScanLine,
  TextSearch,
  Download,
  Trash2,
} from "lucide-react";
import type { useModelStatus } from "../hooks/useModelStatus";
import { useCaptureContext, formatJson } from "../hooks/useSavedCapture";
import type { BenchmarkResult } from "../api/results";
import { useSessionRuns, sessionStats, clearRuns } from "../lib/sessionRuns";
import { labSamples } from "../lib/sampleLibrary";
import { ResearchHighlights } from "../components/research/BenchmarkVisuals";
import { useEffect, useState } from "react";

export function Dashboard() {
  const system = useOutletContext<ReturnType<typeof useModelStatus>>(),
    capture = useCaptureContext();
  const runs = useSessionRuns(),
    stats = sessionStats(runs);
  const benchmark = capture.responses.benchmark as BenchmarkResult | undefined;
  const [download, setDownload] = useState("");
  useEffect(() => {
    const next = URL.createObjectURL(
      new Blob([JSON.stringify(runs, null, 2)], { type: "application/json" }),
    );
    setDownload(next);
    return () => URL.revokeObjectURL(next);
  }, [runs]);
  const latencies = runs
      .slice(0, 12)
      .reverse()
      .map((r) =>
        "decision" in r.result
          ? r.result.total_latency_seconds
          : r.result.latency_seconds.total,
      ),
    maxLatency = Math.max(1, ...latencies);
  return (
    <div className="dashboard-live">
      <header className="dash-title">
        <div>
          <p className="eyebrow">CHEQUEVERIFY / OBSERVATION DESK</p>
          <h1>Your evidence. In focus.</h1>
          <p>
            A live session, an unchanged recogniser, and a clear trail from
            pixels to values.
          </p>
        </div>
        <span className={`readiness-pill ${system.readiness}`}>
          {system.readiness === "ready" ? "Model connected" : "Model not ready"}
        </span>
      </header>
      <section className="session-kpis" aria-label="Live session indicators">
        <div>
          <span>Live requests</span>
          <strong>{stats.requests.toString().padStart(2, "0")}</strong>
          <small>Completed in this browser tab</small>
        </div>
        <div>
          <span>Fields parsed</span>
          <strong>
            {stats.parsed}
            <em> / {stats.fields}</em>
          </strong>
          <small>Strict parsed values, not accuracy</small>
        </div>
        <div>
          <span>Needs human review</span>
          <strong>{stats.review.toString().padStart(2, "0")}</strong>
          <small>Live verification decisions</small>
        </div>
        <div>
          <span>Mean backend time</span>
          <strong>
            {stats.meanSeconds === null ? "—" : stats.meanSeconds.toFixed(2)}
            <em> s</em>
          </strong>
          <small>Measured total per completed request</small>
        </div>
      </section>
      <div className="dash-launch-grid">
        <section className="dash-launch">
          <div>
            <p className="eyebrow">THE LIVE LAB</p>
            <h2>
              Give the model
              <br />
              something new to read.
            </h2>
            <p>
              Pick from {labSamples.length} distinct DEV samples or upload your
              own field crops. Compare methods on the same pixels.
            </p>
            <div className="dash-launch-actions">
              <Link className="button primary" to="/recognize">
                <TextSearch size={18} /> Test a field <ArrowUpRight size={16} />
              </Link>
              <Link to="/verify">
                <ScanLine size={16} /> Compare two amounts
              </Link>
            </div>
          </div>
          <div className="dash-input-stack" aria-hidden="true">
            {labSamples.slice(0, 3).map((s, i) => (
              <div
                key={s.id}
                style={{ transform: `rotate(${(i - 1) * 7}deg)` }}
              >
                <img src={s.image} alt="" />
                <span>{s.synthetic ? "SYNTHETIC" : "HANDWRITING"} / DEV</span>
              </div>
            ))}
          </div>
        </section>
        <section className="polish-card dash-engine">
          <div className="panel-heading">
            <h2>Recognition engine</h2>
            <Cpu size={20} />
          </div>
          <div className="engine-wordmark">
            <img src="/brand/mark-3d.png" alt="ChequeVerify symbol" />
            <div>
              <strong>LoGo-HTR</strong>
              <span>Frozen checkpoint / CPU</span>
            </div>
          </div>
          <dl>
            <div>
              <dt>Parameters</dt>
              <dd>
                {system.info?.parameter_count?.toLocaleString("en-US") ??
                  "Checking…"}
              </dd>
            </div>
            <div>
              <dt>Preparation</dt>
              <dd>Baseline + ATHN</dd>
            </div>
          </dl>
          <button
            className="button secondary"
            disabled={system.loading}
            onClick={() => void system.refresh()}
          >
            <RefreshCw size={15} /> Check connection
          </button>
          <details className="technical">
            <summary>Model provenance</summary>
            <pre>{formatJson(system.info)}</pre>
          </details>
        </section>
      </div>
      <section className="polish-card session-history">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">THIS TAB / LIVE ACTIVITY</p>
            <h2>A record of what you ran.</h2>
          </div>
          <div className="session-actions">
            <a
              href={download}
              download="chequeverify-session.json"
              className="button secondary"
            >
              <Download size={15} /> Export session
            </a>
            <button
              className="icon-button"
              disabled={!runs.length}
              aria-label="Clear session history"
              onClick={clearRuns}
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
        {runs.length ? (
          <>
            <div className="session-latencies">
              <span>Recent backend times</span>
              <div>
                {latencies.map((n, i) => (
                  <i
                    key={i}
                    style={{ height: `${8 + (n / maxLatency) * 34}px` }}
                    title={`${n} s`}
                  />
                ))}
              </div>
              <strong>
                {latencies.at(-1)?.toFixed(2)} s <small>latest</small>
              </strong>
            </div>
            <div className="session-table-wrap">
              <table className="session-table">
                <thead>
                  <tr>
                    <th>Input</th>
                    <th>Method</th>
                    <th>Reading / decision</th>
                    <th>Time</th>
                    <th>Completed</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.slice(0, 8).map((r) => (
                    <tr key={r.id}>
                      <th scope="row">{r.source}</th>
                      <td>
                        {r.result.mode === "baseline" ? "Baseline" : "ATHN"}
                      </td>
                      <td>
                        {"decision" in r.result ? (
                          r.result.decision === "accept" ? (
                            "Amounts agree"
                          ) : r.result.decision === "flag" ? (
                            "Amounts differ"
                          ) : (
                            "Human review"
                          )
                        ) : (
                          <>
                            <strong>{r.result.raw_text || "(empty)"}</strong>
                            <span className="session-parsed">
                              {r.result.parsed_value ?? "Not parsed"}
                            </span>
                          </>
                        )}
                      </td>
                      <td>
                        {("decision" in r.result
                          ? r.result.total_latency_seconds
                          : r.result.latency_seconds.total
                        ).toFixed(2)}{" "}
                        s
                      </td>
                      <td>
                        {new Date(r.at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="session-empty">
            <span>00</span>
            <div>
              <h3>Your first observation starts here.</h3>
              <p>
                Run a field in the live lab. Measured results will populate
                these KPIs and this activity log.
              </p>
            </div>
            <Link to="/recognize">
              Start a live run <ArrowUpRight size={16} />
            </Link>
          </div>
        )}
        <p className="lab-help">
          Response metadata stays in this tab's session storage. Uploaded images
          are not saved. Export results before closing the tab.
        </p>
      </section>
      <section className="dash-sample-section">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">MORE THAN ONE EXAMPLE</p>
            <h2>Different pixels. Different challenges.</h2>
          </div>
          <Link to="/recognize">
            All {labSamples.length} samples <ArrowUpRight size={15} />
          </Link>
        </div>
        <div className="dash-samples">
          {labSamples.slice(0, 3).map((s) => (
            <Link to={`/recognize?sample=${s.id}`} key={s.id}>
              <div>
                <img src={s.image} alt={s.title} />
              </div>
              <span>
                {s.title}
                <ArrowUpRight size={16} />
              </span>
              <small>
                {s.synthetic
                  ? "Font-rendered synthetic field"
                  : "Genuine handwriting"}{" "}
                · DEV
              </small>
            </Link>
          ))}
        </div>
      </section>
      <section className="dashboard-research">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">SEPARATE FROM YOUR SESSION</p>
            <h2>The frozen research, at a glance.</h2>
          </div>
          <Link to="/benchmarks">
            Explore the charts <ArrowUpRight size={15} />
          </Link>
        </div>
        {benchmark ? (
          <ResearchHighlights data={benchmark} />
        ) : (
          <p role="status">{capture.error ?? "Loading recorded research…"}</p>
        )}
      </section>
      <p className="dashboard-context">
        Agreement compares recognised values; it does not establish cheque
        authenticity. No real handwritten cheques were evaluated.
      </p>
    </div>
  );
}
