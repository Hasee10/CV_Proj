import { lazy, Suspense, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, ArrowDownRight, ArrowUp, MoveRight } from "lucide-react";
import type { CaptureState } from "../../hooks/useSavedCapture";
import type { BenchmarkResult, DatasetMetrics } from "../../api/results";
import { decisionCounts, percent } from "../../lib/presentation";

const ResearchSpiral = lazy(() => import("./ResearchXylophone"));

export const researchDatasets = [
  {
    id: "D1_gnhk_words_genuine",
    title: "GNHK words",
    domain: "genuine",
    caption: "Words from genuine handwriting",
  },
  {
    id: "D4_cvl_numeric_genuine",
    title: "CVL digits",
    domain: "genuine",
    caption: "Genuine handwritten digit strings",
  },
  {
    id: "D5_gnhk_numeric_genuine",
    title: "GNHK numeric",
    domain: "genuine",
    caption: "Numeric amounts from genuine handwriting",
  },
  {
    id: "D5_gnhk_words_genuine",
    title: "GNHK number words",
    domain: "genuine",
    caption: "Written amounts from genuine handwriting",
  },
  {
    id: "D6_syn_numeric_SYNTHETIC",
    title: "Synthetic figures",
    domain: "synthetic",
    caption: "Font-rendered numeric cheque fields",
  },
  {
    id: "D6_syn_words_SYNTHETIC",
    title: "Synthetic words",
    domain: "synthetic",
    caption: "Font-rendered written cheque fields",
  },
] as const;

export function CerSculpture({
  metrics,
  title,
  synthetic,
}: {
  metrics: DatasetMetrics;
  title: string;
  synthetic: boolean;
}) {
  // A fixed scale within each domain. Constant extrusion is decorative; front
  // face height alone encodes CER, with direct values and an explicit axis.
  const domain = synthetic ? 1.1 : 0.5;
  const ticks = synthetic
    ? [0, 0.25, 0.5, 0.75, 1, 1.1]
    : [0, 0.1, 0.2, 0.3, 0.4, 0.5];
  const base = 200,
    scale = 125 / domain;
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="640"
      height="250"
      fontFamily="Arial, sans-serif"
      className="cer-sculpture"
      viewBox="0 0 640 250"
      role="img"
      aria-label={`${title}: baseline CER ${percent(metrics.cer.baseline)}, ATHN ${percent(metrics.cer.proposed)}. Lower is better. Axis zero to ${percent(domain)}.`}
    >
      <title>{`${title}: character error rate comparison`}</title>
      <desc>
        Bar front-face heights encode the two saved CER values. Extrusion is
        decorative. CER may exceed 100% because of insertion errors.
      </desc>
      <path
        d="M92 200H580l32 -27H124Z"
        fill="#e0e8d5"
        fillOpacity=".035"
        stroke="#b1c2a3"
        strokeOpacity=".18"
      />
      {ticks.map((tick) => (
        <g key={tick}>
          <line
            x1="95"
            x2="583"
            y1={base - tick * scale}
            y2={base - tick * scale}
            stroke="#adc2a1"
            strokeOpacity=".14"
            strokeDasharray="2 5"
          />
          <text
            x="78"
            y={base - tick * scale + 4}
            textAnchor="end"
            fill="#8da38c"
            fontSize="10"
          >
            {Math.round(tick * 100)}%
          </text>
        </g>
      ))}
      {[
        {
          label: "Baseline",
          value: metrics.cer.baseline,
          x: 200,
          front: "#7c8e87",
          side: "#536b61",
          top: "#a8bab0",
        },
        {
          label: "ATHN",
          value: metrics.cer.proposed,
          x: 416,
          front: "#bbd39d",
          side: "#789c67",
          top: "#e0ebc9",
        },
      ].map((bar) => {
        const y = base - bar.value * scale;
        return (
          <g key={bar.label}>
            <path d={`M${bar.x} ${y}h76v${base - y}h-76Z`} fill={bar.front} />
            <path
              d={`M${bar.x + 76} ${y}l26 -22v${base - y}l-26 22Z`}
              fill={bar.side}
            />
            <path d={`M${bar.x} ${y}l26 -22h76l-26 22Z`} fill={bar.top} />
            <text
              x={bar.x + 49}
              y={y - 37}
              textAnchor="middle"
              fill="#edf2e1"
              fontSize="24"
              letterSpacing="-1"
            >
              {percent(bar.value)}
            </text>
            <text
              x={bar.x + 42}
              y="232"
              textAnchor="middle"
              fill="#c4d4b7"
              fontSize="12"
            >
              {bar.label}
            </text>
          </g>
        );
      })}
      <text x="340" y="248" textAnchor="middle" fill="#8da38c" fontSize="10">
        Character error rate · lower is better
      </text>
    </svg>
  );
}

export function ResearchEvidence({ capture }: { capture: CaptureState }) {
  const [selected, setSelected] = useState<string>(researchDatasets[0].id);
  const benchmark = capture.responses.benchmark as BenchmarkResult | undefined;
  const definition = researchDatasets.find((d) => d.id === selected)!;
  const metrics = benchmark?.datasets[selected];
  const synthetic = definition.domain === "synthetic";
  const pairReview =
    benchmark?.pairs.syn_all_SYNTHETIC.proposed.decisions.review;
  const pairTotal = benchmark
    ? decisionCounts(benchmark.pairs.syn_all_SYNTHETIC.proposed).reduce(
        (sum, item) => sum + item.count,
        0,
      )
    : null;
  return (
    <section
      className="landing-evidence evidence-lab spiral-lab"
      id="evidence"
      aria-labelledby="evidence-title"
    >
      <div className="spiral-heading">
        <div>
          <p className="study-label">
            THE RESEARCH / SIX DATASETS, TWO PREPARATIONS
          </p>
          <h2 id="evidence-title">
            Where scale helps.
            <br />
            <span>Where it falls short.</span>
          </h2>
        </div>
        <span className="spiral-source">
          One frozen recogniser.
          <br />
          Six measured comparisons.
        </span>
      </div>
      {benchmark && metrics ? (
        <>
          <div className="spiral-lab-grid">
            <div className="spiral-visual">
              <Suspense
                fallback={
                  <div className="spiral-loading">
                    Opening the glass xylophone…
                  </div>
                }
              >
                <ResearchSpiral
                  selected={researchDatasets.findIndex(
                    (d) => d.id === selected,
                  )}
                  onSelect={(index) => setSelected(researchDatasets[index].id)}
                />
              </Suspense>
            </div>
            <div className="spiral-readout">
              <div
                className="research-domain-toggle"
                role="group"
                aria-label="Research data source"
              >
                {(["genuine", "synthetic"] as const).map((domain) => (
                  <button
                    key={domain}
                    aria-pressed={definition.domain === domain}
                    onClick={() =>
                      setSelected(
                        researchDatasets.find((d) => d.domain === domain)!.id,
                      )
                    }
                  >
                    {domain === "genuine"
                      ? "Genuine handwriting"
                      : "Synthetic fields"}
                  </button>
                ))}
              </div>
              <nav
                className="spiral-datasets"
                aria-label="Select a research dataset"
              >
                {researchDatasets.map((d, index) => {
                  const data = benchmark.datasets[d.id],
                    regression = data.cer.proposed > data.cer.baseline;
                  return (
                    <button
                      key={d.id}
                      hidden={d.domain !== definition.domain}
                      aria-pressed={selected === d.id}
                      onClick={() => setSelected(d.id)}
                    >
                      <small>
                        {String(index + 1).padStart(2, "0")} /{" "}
                        {d.domain === "genuine" ? "GENUINE" : "SYNTHETIC"}
                      </small>
                      <span>
                        {d.title}
                        <i
                          aria-label={
                            regression ? "CER increased" : "CER decreased"
                          }
                        >
                          {regression ? (
                            <ArrowUp size={12} />
                          ) : (
                            <ArrowDownRight size={12} />
                          )}
                        </i>
                      </span>
                    </button>
                  );
                })}
              </nav>
              <div className="spiral-measurement" aria-live="polite">
                <div className="spiral-measure-heading">
                  <div>
                    <span className={`research-domain ${definition.domain}`}>
                      {synthetic
                        ? "SYNTHETIC / FONT RENDERED"
                        : "GENUINE / HANDWRITTEN"}
                    </span>
                    <h3>{definition.title}</h3>
                  </div>
                  <span>{metrics.n_eligible} eligible crops</span>
                </div>
                <p className="spiral-metric-label">
                  Character error rate <span>Lower is better</span>
                </p>
                <div className="spiral-values">
                  <div>
                    <small>Baseline</small>
                    <strong>{percent(metrics.cer.baseline)}</strong>
                  </div>
                  <MoveRight size={22} aria-label="to" />
                  <div>
                    <small>ATHN</small>
                    <strong>{percent(metrics.cer.proposed)}</strong>
                  </div>
                </div>
                <div
                  className="spiral-meter"
                  role="img"
                  aria-label={`CER on a shared zero to ${synthetic ? "110" : "50"}% scale: baseline ${percent(metrics.cer.baseline)}, ATHN ${percent(metrics.cer.proposed)}.`}
                >
                  {[metrics.cer.baseline, metrics.cer.proposed].map(
                    (value, index) => (
                      <div key={index}>
                        <i
                          style={{
                            width: `${(value / (synthetic ? 1.1 : 0.5)) * 100}%`,
                          }}
                        />
                      </div>
                    ),
                  )}
                </div>
                <div className="spiral-exact">
                  <span>
                    {metrics.value_exact
                      ? "Exact parsed values"
                      : "Exact transcriptions"}
                  </span>
                  <strong>
                    {metrics.value_exact?.baseline ?? metrics.exact.baseline}
                    <MoveRight size={16} />
                    {metrics.value_exact?.proposed ?? metrics.exact.proposed}
                    <small>
                      / {metrics.value_exact?.n ?? metrics.n_eligible}
                    </small>
                  </strong>
                </div>
                <p className="spiral-verdict">
                  {metrics.cer.proposed > metrics.cer.baseline
                    ? "CER increased here. Scale does not improve every dataset."
                    : synthetic
                      ? "Synthetic gain; real handwriting performance is not established."
                      : "Subset improvement; the overall genuine-handwriting change was not statistically significant."}
                </p>
              </div>
            </div>
          </div>
          <div className="spiral-limits">
            <div>
              <strong>
                {pairReview ?? "Not reported"}
                <small>/ {pairTotal ?? "Not reported"}</small>
              </strong>
              <span>
                Synthetic pairs → human review
                <small>
                  {benchmark.pairs.syn_all_SYNTHETIC.proposed.n_eligible}{" "}
                  eligible ·{" "}
                  {benchmark.pairs.syn_all_SYNTHETIC.proposed.unresolved}{" "}
                  unresolved
                </small>
              </span>
            </div>
            <div>
              <strong>
                {
                  benchmark.datasets.D6_syn_words_SYNTHETIC.value_exact
                    ?.proposed
                }
                <small>
                  / {benchmark.datasets.D6_syn_words_SYNTHETIC.value_exact?.n}
                </small>
              </strong>
              <span>
                Written synthetic amounts
                <br />
                exactly parsed with ATHN
              </span>
            </div>
            <p>
              No real handwritten cheques were evaluated. The overall
              genuine-handwriting change was not statistically significant.
            </p>
          </div>
          <div className="spiral-footer">
            <span>
              Saved locked-test results · same frozen LoGo-HTR · no evaluation
              runs here
            </span>
            <Link to="/benchmarks">
              All metrics & limitations <ArrowUpRight size={15} />
            </Link>
          </div>
        </>
      ) : (
        <p role="status">
          {capture.error ?? "Loading the saved research metrics…"}
        </p>
      )}
    </section>
  );
}
