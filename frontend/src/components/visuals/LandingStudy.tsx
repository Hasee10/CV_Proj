import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  ScanLine,
  CaseSensitive,
  GitCompareArrows,
} from "lucide-react";
import type { CaptureState } from "../../hooks/useSavedCapture";
import type { VerifyResult } from "../../api/results";
import { roiRect } from "../../lib/presentation";

const cases = [
  { id: "sheet_accept", label: "Agreement" },
  { id: "sheet_flag", label: "Mismatch" },
  { id: "sheet_review", label: "Human review" },
] as const;
const decisions = {
  accept: {
    title: "Amounts agree",
    symbol: "=",
    description: "Both recognised fields parse to the same value.",
  },
  flag: {
    title: "Amounts differ",
    symbol: "≠",
    description: "Both fields parse, but their recognised values differ.",
  },
  review: {
    title: "Needs human review",
    symbol: "?",
    description:
      "The written reading cannot be parsed. The comparison stays unresolved.",
  },
};

function WorkflowCrop({
  src,
  box,
  field,
}: {
  src: string;
  box: number[];
  field: "numeric" | "written";
}) {
  const [size, setSize] = useState<{ width: number; height: number } | null>(
    null,
  );
  const bounds = roiRect(box);
  return (
    <figure className={`trace-crop ${field}`}>
      <figcaption>
        <span>{field === "numeric" ? "Figures" : "Words"}</span>
        <small>
          {bounds.width} × {bounds.height} px
        </small>
      </figcaption>
      <img
        className="trace-image-loader"
        src={src}
        alt=""
        aria-hidden="true"
        onLoad={(event) =>
          setSize({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          })
        }
      />
      {size ? (
        <svg
          viewBox={`${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}`}
          role="img"
          aria-label={`Original ${field} crop from the selected constructed DEV sheet`}
        >
          <image href={src} width={size.width} height={size.height} />
        </svg>
      ) : (
        <span className="trace-crop-loading">Loading original pixels…</span>
      )}
    </figure>
  );
}

export function WorkflowSection({ capture }: { capture: CaptureState }) {
  const [selected, setSelected] = useState<string>(cases[0].id);
  const record = capture.manifest?.records.find((r) => r.id === selected);
  const result = capture.responses[selected] as VerifyResult | undefined;
  const decision = result ? decisions[result.decision] : null;
  return (
    <section
      className="landing-workflow workflow-trace"
      id="workflow"
      aria-labelledby="workflow-title"
    >
      <div className="trace-section-heading">
        <div>
          <p className="section-label">THE WORKFLOW / FOLLOW THE EVIDENCE</p>
          <h2 id="workflow-title">
            From a handwritten field
            <br />
            <span>to a traceable result.</span>
          </h2>
        </div>
        <p>
          Two selected fields. Their original pixels, unedited readings, and
          parsed values—connected to one inspectable decision.
        </p>
      </div>
      <div className="trace-toolbar">
        <p>
          <i aria-hidden="true" />
          Explore a recorded comparison
        </p>
        <div role="group" aria-label="Choose a recorded workflow example">
          {cases.map((item) => (
            <button
              key={item.id}
              aria-pressed={selected === item.id}
              onClick={() => setSelected(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      {record?.image && result?.rois && decision ? (
        <>
          <div className="trace-pipeline">
            <section
              className="trace-stage trace-input"
              aria-labelledby="trace-input-title"
            >
              <div className="trace-step-label">
                <span>01 / SELECT</span>
                <ScanLine size={18} aria-hidden="true" />
              </div>
              <h3 id="trace-input-title">Keep the pixels.</h3>
              <p>Original regions, taken from the saved input.</p>
              <div className="trace-crop-stack">
                <WorkflowCrop
                  key={`${selected}-numeric`}
                  src={record.image}
                  box={result.rois.numeric_px}
                  field="numeric"
                />
                <WorkflowCrop
                  key={`${selected}-written`}
                  src={record.image}
                  box={result.rois.written_px}
                  field="written"
                />
              </div>
            </section>
            <section
              className="trace-stage trace-recognition"
              aria-labelledby="trace-reading-title"
            >
              <div className="trace-step-label">
                <span>02 / RECOGNISE & PARSE</span>
                <CaseSensitive size={19} aria-hidden="true" />
              </div>
              <h3 id="trace-reading-title">Make the reading explicit.</h3>
              <p>Raw model text stays beside the parsed value.</p>
              <div className="trace-readings" aria-live="polite">
                {(["numeric", "written"] as const).map((field) => (
                  <div className={`trace-reading ${field}`} key={field}>
                    <span>{field === "numeric" ? "Figures" : "Words"}</span>
                    <div className="trace-reading-values">
                      <div>
                        <small>Raw reading</small>
                        <strong
                          className={
                            result[field].raw_text.length > 9
                              ? "long-reading"
                              : ""
                          }
                        >
                          {result[field].raw_text || "(empty)"}
                        </strong>
                      </div>
                      <span aria-hidden="true">→</span>
                      <div>
                        <small>Parsed value</small>
                        <strong
                          className={
                            result[field].parsed_value === null
                              ? "unparsed-reading"
                              : ""
                          }
                        >
                          {result[field].parsed_value ?? "Not parsed"}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
            <section
              className={`trace-stage trace-decision ${result.decision}`}
              aria-labelledby="trace-decision-title"
            >
              <div className="trace-step-label">
                <span>03 / COMPARE</span>
                <GitCompareArrows size={18} aria-hidden="true" />
              </div>
              <svg
                className="trace-decision-diagram"
                viewBox="0 0 360 120"
                role="img"
                aria-label={`Recognised values ${result.numeric.parsed_value ?? "not parsed"} and ${result.written.parsed_value ?? "not parsed"}: ${decision.title}`}
              >
                <path
                  className="trace-signal"
                  d="M130 28h30l33 32M130 92h30l33 -32M260 60h75m-5 -5l5 5 -5 5"
                  stroke="#b8cea1"
                  fill="none"
                />
                {(["numeric", "written"] as const).map((field, index) => (
                  <g className={`trace-png-node node-${index}`} key={field}>
                    <image
                      href="/workflow/input-tile.png"
                      x="0"
                      y={index === 0 ? 0 : 64}
                      width="145"
                      height="56"
                      preserveAspectRatio="none"
                    />
                    <text
                      x="72.5"
                      y={index === 0 ? 33 : 97}
                      textAnchor="middle"
                      fill="#204434"
                      fontSize={result[field].parsed_value === null ? 13 : 16}
                    >
                      {result[field].parsed_value ?? "Not parsed"}
                    </text>
                  </g>
                ))}
                <g className="trace-png-hub">
                  <image
                    href="/workflow/comparison-hub.png"
                    x="182"
                    y="15"
                    width="90"
                    height="90"
                  />
                  <text
                    x="227"
                    y="69"
                    textAnchor="middle"
                    fill="#24432f"
                    fontSize="29"
                  >
                    {decision.symbol}
                  </text>
                </g>
              </svg>
              <div className="trace-decision-copy" aria-live="polite">
                <h3 id="trace-decision-title">{decision.title}</h3>
                <p>{decision.description}</p>
              </div>
              <Link to={`/verify?example=${selected}`}>
                Inspect this comparison{" "}
                <ArrowUpRight size={16} aria-hidden="true" />
              </Link>
            </section>
          </div>
          <div className="trace-provenance">
            <p>
              <span>
                {record.synthetic
                  ? "Synthetic font-rendered input"
                  : "Genuine handwriting"}
              </span>{" "}
              · Constructed DEV pair · {result.mode}
            </p>
            <a href={record.response} target="_blank" rel="noreferrer">
              Saved request <code>{result.request_id}</code>{" "}
              <ArrowUpRight size={12} aria-hidden="true" />
            </a>
          </div>
          <p className="trace-authenticity">
            Agreement compares recognised amounts. It does not establish cheque
            authenticity.
          </p>
        </>
      ) : (
        <p className="trace-loading" role="status">
          {capture.error ?? "Loading the recorded comparison…"}
        </p>
      )}
    </section>
  );
}
