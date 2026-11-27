import { useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api, isModelInfo } from "../api/client";
import type { BenchmarkResult, PairMetrics } from "../api/results";
import { formatJson, useCaptureContext } from "../hooks/useSavedCapture";
import { CaptureProvenance } from "../components/results/ResultDetails";
import { BenchmarkVisuals } from "../components/research/BenchmarkVisuals";
const names: Record<string, string> = {
  D1_gnhk_words_genuine: "GNHK words",
  D4_cvl_numeric_genuine: "CVL digit strings",
  D5_gnhk_numeric_genuine: "GNHK numeric crops",
  D5_gnhk_words_genuine: "GNHK number words",
  D6_syn_numeric_SYNTHETIC: "Synthetic numeric fields",
  D6_syn_words_SYNTHETIC: "Synthetic written fields",
  gnhk_pairs_genuine_constructed: "Constructed pairs of genuine GNHK crops",
  syn_all_SYNTHETIC: "All synthetic pairs",
  syn_natural_SYNTHETIC: "Natural synthetic pairs",
  syn_constructed_SYNTHETIC: "Constructed synthetic pairs",
};
const show = (v: unknown) =>
  v === null ? "n/a" : v === undefined ? "Not reported" : String(v);
function Confusion({ data }: { data: PairMetrics }) {
  return (
    <table className="confusion-table">
      <caption>Ground-truth relation → model decision</caption>
      <thead>
        <tr>
          <th scope="col">Relation</th>
          {["accept", "flag", "review"].map((c) => (
            <th key={c} scope="col">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {["match", "mismatch"].map((r) => (
          <tr key={r}>
            <th scope="row">{r}</th>
            {["accept", "flag", "review"].map((c) => (
              <td key={c}>{data.confusion[`${r}->${c}`] ?? 0}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
export function Benchmark() {
  const capture = useCaptureContext();
  const [live, setLive] = useState<BenchmarkResult | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null),
    running = useRef(false);
  useEffect(() => () => controller.current?.abort(), []);
  async function refresh() {
    if (running.current) return;
    running.current = true;
    const c = new AbortController();
    controller.current = c;
    setBusy(true);
    setError(null);
    try {
      const data = await api.benchmark(c.signal);
      if (!c.signal.aborted) setLive(data);
    } catch (e) {
      if (!c.signal.aborted)
        setError(e instanceof Error ? e.message : "Unable to fetch benchmark.");
    } finally {
      running.current = false;
      if (!c.signal.aborted) setBusy(false);
    }
  }
  const data =
    live ?? (capture.responses.benchmark as BenchmarkResult | undefined);
  const model = capture.responses["model-info"];
  const record = capture.manifest?.records.find((r) => r.id === "benchmark");
  if (capture.loading)
    return <p role="status">Loading the captured research results…</p>;
  if (!data || !record || !capture.manifest)
    return (
      <div className="error-list" role="alert">
        {capture.error ?? "No saved research response is available."}
      </div>
    );
  return (
    <div className="benchmark-page">
      <header className="results-heading">
        <p className="eyebrow">FROZEN RESEARCH / LOCKED TEST SPLIT</p>
        <h1>Research benchmarks</h1>
        <p>
          Baseline and ATHN, presented exactly from the saved backend metrics.
          These measurements describe the research method, not product accuracy.
        </p>
      </header>
      <div className="capture-source-banner">
        <span className="capture-chip">
          {live ? "Live API · saved metrics file" : "Saved API capture"}
        </span>
        <span>Split: {data.split}</span>
        <button
          className="button secondary"
          disabled={busy}
          onClick={() => void refresh()}
        >
          <RefreshCw size={17} aria-hidden="true" />
          {busy ? "Reading metrics…" : "Refresh from backend"}
        </button>
      </div>
      {error && (
        <div className="error-list" role="alert">
          {error} The earlier capture remains below.
        </div>
      )}
      <p className="result-help">
        Source: <code>{data.source}</code>. This endpoint reads the saved file;
        no evaluation is rerun. Percentages below are presentation formatting;
        raw values remain in the detailed tables. CER can exceed 1 due to
        insertion errors.
      </p>
      <BenchmarkVisuals data={data} />
      <details className="benchmark-tables polish-card">
        <summary>
          Detailed metrics, confusion matrices &amp; original source values
        </summary>
        {[false, true].map((synthetic) => (
          <section className="benchmark-group" key={String(synthetic)}>
            <div className="benchmark-group-heading">
              <span className="capture-chip">
                {synthetic ? "SYNTHETIC" : "GENUINE HANDWRITING"}
              </span>
              <h2>
                {synthetic
                  ? "Font-rendered cheque fields"
                  : "Handwritten words and digits"}
              </h2>
            </div>
            <div
              className="results-table-wrap"
              role="region"
              aria-label={`${synthetic ? "Synthetic" : "Genuine"} recognition metrics`}
              tabIndex={0}
            >
              <table className="results-table">
                <caption>
                  Recognition results — values as returned by the API
                </caption>
                <thead>
                  <tr>
                    {[
                      "Dataset",
                      "Mode",
                      "Items",
                      "CER",
                      "WER",
                      "Exact",
                      "Exact rate",
                      "Value exact",
                      "Value items",
                      "Parseable",
                    ].map((h) => (
                      <th scope="col" key={h}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.datasets)
                    .filter(([key]) => key.includes("SYNTHETIC") === synthetic)
                    .flatMap(([key, d]) =>
                      (["baseline", "proposed"] as const).map((mode) => (
                        <tr key={key + mode}>
                          <th scope="row">{names[key] ?? key}</th>
                          <td>{mode === "proposed" ? "ATHN" : mode}</td>
                          <td>{d.n_eligible}</td>
                          <td>{show(d.cer[mode])}</td>
                          <td>{show(d.wer[mode])}</td>
                          <td>{show(d.exact[mode])}</td>
                          <td>{show(d.exact_rate[mode])}</td>
                          <td>{show(d.value_exact?.[mode])}</td>
                          <td>{show(d.value_exact?.n)}</td>
                          <td>{show(d.value_exact?.parseable?.[mode])}</td>
                        </tr>
                      )),
                    )}
                </tbody>
              </table>
            </div>
            <details className="response-detail">
              <summary>Reported changes and complete dataset metrics</summary>
              <pre>
                {formatJson(
                  Object.fromEntries(
                    Object.entries(data.datasets).filter(
                      ([key]) => key.includes("SYNTHETIC") === synthetic,
                    ),
                  ),
                )}
              </pre>
            </details>
          </section>
        ))}
        <section className="benchmark-group">
          <h2>Pair decisions</h2>
          <p className="result-help">
            Genuine pair results use constructed pairs of genuine crops, not
            real cheques. No real handwritten cheques were available.
            Match/mismatch definitions follow the{" "}
            <a
              href={`https://github.com/Hasee10/CV_Proj/blob/${capture.manifest.source_git_commit}/artifacts/M8/FINAL_EVALUATION_REPORT.md`}
              target="_blank"
              rel="noreferrer"
            >
              evaluation report
            </a>
            .
          </p>
          {[false, true].map((synthetic) => (
            <div className="pair-group" key={String(synthetic)}>
              <h3>
                {synthetic
                  ? "Synthetic pairs"
                  : "Genuine handwriting · constructed pairs"}
              </h3>
              <div
                className="results-table-wrap"
                role="region"
                aria-label={`${synthetic ? "Synthetic" : "Genuine"} pair decisions`}
                tabIndex={0}
              >
                <table className="results-table">
                  <thead>
                    <tr>
                      {[
                        "Group",
                        "Mode",
                        "Eligible pairs",
                        "Unresolved",
                        "Accept",
                        "Flag",
                        "Review",
                        "Review rate",
                        "Decision coverage",
                        "Incorrect acceptance",
                        "Incorrect rejection",
                        "Mismatch detection",
                        "Auto-accepted matches",
                      ].map((h) => (
                        <th scope="col" key={h}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.pairs)
                      .filter(
                        ([key]) => key.includes("SYNTHETIC") === synthetic,
                      )
                      .flatMap(([key, p]) =>
                        (["baseline", "proposed"] as const).map((mode) => (
                          <tr key={key + mode}>
                            <th scope="row">{names[key] ?? key}</th>
                            <td>{mode === "proposed" ? "ATHN" : mode}</td>
                            <td>{p[mode].n_eligible}</td>
                            <td>{p[mode].unresolved}</td>
                            {(["accept", "flag", "review"] as const).map(
                              (d) => (
                                <td key={d}>{p[mode].decisions[d] ?? 0}</td>
                              ),
                            )}
                            <td>{show(p[mode].review_rate)}</td>
                            <td>{show(p[mode].decision_coverage)}</td>
                            <td>{show(p[mode].incorrect_acceptance_rate)}</td>
                            <td>{show(p[mode].incorrect_rejection_rate)}</td>
                            <td>{show(p[mode].explicit_mismatch_detection)}</td>
                            <td>{show(p[mode].auto_accepted_matches)}</td>
                          </tr>
                        )),
                      )}
                  </tbody>
                </table>
              </div>
              {Object.entries(data.pairs)
                .filter(([key]) => key.includes("SYNTHETIC") === synthetic)
                .map(([key, p]) => (
                  <details className="response-detail" key={key}>
                    <summary>{names[key] ?? key} — confusion & details</summary>
                    <div className="confusion-grid">
                      {(["baseline", "proposed"] as const).map((mode) => (
                        <div key={mode}>
                          <h4>{mode}</h4>
                          <Confusion data={p[mode]} />
                        </div>
                      ))}
                    </div>
                    <pre>{formatJson(p)}</pre>
                  </details>
                ))}
            </div>
          ))}
        </section>
      </details>
      <details className="research-boundaries additional-limits">
        <summary>
          Research context, historical latency &amp; source report
        </summary>
        <h2>Read the limits alongside the numbers.</h2>
        <p>
          Decision counts include unresolved pairs; eligible-pair metrics and
          confusion tables exclude them. The API reports 146 eligible and 18
          unresolved synthetic pairs, with 164 review decisions. These counts
          retain their original denominators.
        </p>
        <p>
          Every synthetic pair went to review under both methods because no
          synthetic written amount parsed. The genuine-handwriting change was
          not statistically significant; that does not establish equivalence.
        </p>
        <p>
          Confidence intervals are omitted here because the API does not return
          them. They are available in the evaluation report. Enlarged written
          lines can be slow: the recorded test median was 0.251 s baseline and
          0.294 s ATHN; 5 of 89 enlarged synthetic written lines exceeded 120 s,
          with a maximum of 419 s. These are historical measurements, not this
          capture's timings.
        </p>
        {isModelInfo(model) && (
          <ul>
            {model.limitations.map((l) => (
              <li key={l}>{l}</li>
            ))}
          </ul>
        )}
      </details>
      <details className="response-detail">
        <summary>Frozen proposed configuration</summary>
        <pre>{formatJson(data.proposed_config)}</pre>
      </details>
      <CaptureProvenance record={record} manifest={capture.manifest} />
    </div>
  );
}
