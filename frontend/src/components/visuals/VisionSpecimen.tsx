import { lazy, Suspense, useState } from "react";
import { ArrowUpRight, Box, Image, Ruler } from "lucide-react";
import type { CaptureState } from "../../hooks/useSavedCapture";
import type { BenchmarkResult, FieldResult } from "../../api/results";
import { sampleStudies } from "../../generated/sampleStudies";
const PixelRelief = lazy(() => import("./PixelRelief"));

export function ScaleDiagram({
  baseline,
  proposed,
  targetHeight,
  tone = "dark",
}: {
  baseline: FieldResult;
  proposed: FieldResult;
  targetHeight?: number;
  tone?: "dark" | "light";
}) {
  const [inputH, inputW] = baseline.model_input_shape.slice(-2),
    [outputH, outputW] = proposed.model_input_shape.slice(-2);
  const maxWidth = 330,
    ratio = maxWidth / Math.max(inputW, outputW);
  const ink = tone === "light" ? "#244c36" : "#dce8ca";
  const muted = tone === "light" ? "#5f7b64" : "#9aad9a";
  const line = tone === "light" ? "#7f9c6d" : "#b7cda0";
  const inputInk = tone === "light" ? "#537c6c" : "#a9c8ba";
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="520"
      height="275"
      fontFamily="Arial, sans-serif"
      className="scale-diagram"
      viewBox="0 0 520 275"
      role="img"
      aria-label={`Recorded image dimensions: baseline ${inputW} by ${inputH} pixels; ATHN ${outputW} by ${outputH} pixels. Scale diagram, not a processed-image preview.`}
    >
      <defs>
        <pattern
          id="scale-pixel-grid"
          width="11"
          height="11"
          patternUnits="userSpaceOnUse"
        >
          <path
            d="M11 0H0V11"
            fill="none"
            stroke={line}
            strokeOpacity=".13"
            strokeWidth=".7"
          />
        </pattern>
      </defs>
      <rect
        x="95"
        y="60"
        width={outputW * ratio}
        height={outputH * ratio}
        fill="url(#scale-pixel-grid)"
        stroke={line}
        strokeWidth="1.5"
      />
      <rect
        x="95"
        y="60"
        width={inputW * ratio}
        height={inputH * ratio}
        fill="#93b7a9"
        fillOpacity=".3"
        stroke="#9bc6b8"
      />
      <path
        d={`M95 43H${95 + outputW * ratio}M95 38v10M${95 + outputW * ratio} 38v10`}
        fill="none"
        stroke={line}
      />
      <text x="260" y="28" textAnchor="middle" fill={ink} fontSize="13">
        ATHN · {outputW} × {outputH} px
      </text>
      <path
        d={`M${95 + inputW * ratio} ${60 + inputH * ratio}l40 65h110`}
        fill="none"
        stroke="#98bdaf"
        strokeWidth="1"
      />
      <text x="260" y="180" textAnchor="middle" fill={inputInk} fontSize="12">
        Baseline · {inputW} × {inputH} px
      </text>
      <text x="260" y="218" textAnchor="middle" fill={ink} fontSize="23">
        {String(proposed.preprocessing.scale)}× scale
      </text>
      <text x="260" y="244" textAnchor="middle" fill={muted} fontSize="10">
        Estimated text height{" "}
        {String(proposed.preprocessing.estimated_text_height)} px
        {targetHeight ? ` · target ${targetHeight} px` : ""}
      </text>
    </svg>
  );
}

export function VisionSpecimen({ capture }: { capture: CaptureState }) {
  const [view, setView] = useState<"relief" | "original" | "scale">("relief");
  const [sampleIndex, setSampleIndex] = useState(1);
  const study = sampleStudies[sampleIndex];
  const baseline = study.responses.baseline.result as unknown as FieldResult;
  const proposed = study.responses.proposed.result as unknown as FieldResult;
  const record = { image: study.image };
  const configuration = (
    capture.responses.benchmark as BenchmarkResult | undefined
  )?.proposed_config;
  const targetHeight =
    typeof configuration?.target === "number"
      ? configuration.target
      : undefined;
  if (!baseline || !proposed || !record?.image)
    return (
      <aside
        className="cv-specimen unified-specimen"
        aria-label="Recorded handwriting study"
      >
        <p role="status">
          {capture.error ?? "Loading the recorded handwriting study…"}
        </p>
      </aside>
    );
  return (
    <aside
      className="cv-specimen unified-specimen"
      aria-labelledby="specimen-title"
    >
      <div className="study-topline">
        <span className="study-label">THE PIXELS BEHIND THE READING</span>
        <span className="recorded-tag">
          <i />
          Recorded DEV example
        </span>
      </div>
      <h2 id="specimen-title" className="study-title">
        One crop. <span>Two preparations.</span>
      </h2>
      <div
        className="specimen-samples"
        role="group"
        aria-label="Recorded development sample"
      >
        {sampleStudies.map((sample, index) => (
          <button
            key={sample.id}
            aria-pressed={sampleIndex === index}
            onClick={() => setSampleIndex(index)}
          >
            {sample.id === "digits"
              ? "Digit string"
              : sample.id === "handwriting"
                ? "Handwritten field"
                : "Synthetic field"}
          </button>
        ))}
      </div>
      <div
        className="study-tabs"
        role="group"
        aria-label="Explore the recorded input"
      >
        {(
          [
            { id: "relief", label: "Pixel relief", Icon: Box },
            { id: "original", label: "Original crop", Icon: Image },
            { id: "scale", label: "ATHN scale", Icon: Ruler },
          ] as const
        ).map(({ id, label, Icon }) => (
          <button
            key={id}
            aria-pressed={view === id}
            onClick={() => setView(id)}
          >
            <Icon size={13} aria-hidden="true" />
            {label}
          </button>
        ))}
      </div>
      <div className={`study-scene view-${view}`}>
        {view === "relief" ? (
          <Suspense
            fallback={<p className="study-loading">Building the pixel view…</p>}
          >
            <PixelRelief src={record.image} />
          </Suspense>
        ) : view === "original" ? (
          <figure className="study-original">
            <img
              src={record.image}
              alt={`Unchanged ${study.synthetic ? "synthetic" : "genuine handwritten"} numeric DEV crop`}
            />
            <figcaption>
              {baseline.image?.width} × {baseline.image?.height} px · unchanged
              source
            </figcaption>
          </figure>
        ) : (
          <ScaleDiagram
            baseline={baseline}
            proposed={proposed}
            targetHeight={targetHeight}
            tone="light"
          />
        )}
        <div className="study-scene-caption">
          {view === "relief" ? (
            <>
              <span>Paper-relative ink height</span>
              <span>Drag / arrow keys ↔</span>
            </>
          ) : view === "original" ? (
            <>
              <span>
                {study.synthetic ? "Synthetic" : "Handwritten"} numeric field
              </span>
              <span>Original pixels</span>
            </>
          ) : (
            <>
              <span>
                Recorded scale diagram · not a processed-image preview
              </span>
              <a
                href={study.responses.proposed.path}
                target="_blank"
                rel="noreferrer"
              >
                Open SVG ↗
              </a>
            </>
          )}
        </div>
      </div>
      <div className="study-fork" aria-hidden="true">
        <span>Same frozen LoGo-HTR</span>
        <svg viewBox="0 0 600 52" preserveAspectRatio="none">
          <path
            d="M300 14v8M150 46V31q0-9 9-9h282q9 0 9 9v15"
            fill="none"
            stroke="currentColor"
          />
          <circle cx="150" cy="46" r="2" />
          <circle cx="450" cy="46" r="2" />
        </svg>
      </div>
      <div className="study-results" aria-label="Actual saved model readings">
        <div className="study-result baseline">
          <span className="study-method">
            <i />
            Baseline
          </span>
          <span className="study-dimensions">
            {baseline.model_input_shape.at(-1)} ×{" "}
            {baseline.model_input_shape.at(-2)} px input
          </span>
          <strong>{baseline.raw_text}</strong>
          <small>Parsed {baseline.parsed_value ?? "Not parsed"}</small>
        </div>
        <div className="study-result athn">
          <span className="study-method">
            <i />
            With ATHN{" "}
            <span className="study-scale-tag">
              {String(proposed.preprocessing.scale)}×
            </span>
          </span>
          <span className="study-dimensions">
            {proposed.model_input_shape.at(-1)} ×{" "}
            {proposed.model_input_shape.at(-2)} px input
          </span>
          <strong>
            {proposed.raw_text.split("").map((char, i) => (
              <span
                key={i}
                className={
                  char !== baseline.raw_text[i] ? "changed-reading" : ""
                }
              >
                {char}
              </span>
            ))}
          </strong>
          <small>Parsed {proposed.parsed_value ?? "Not parsed"}</small>
        </div>
      </div>
      <div className="study-source">
        <p>
          {study.synthetic ? "Synthetic" : "Genuine handwriting"} DEV example,
          not an accuracy claim. Relief shows pixel intensity, not model
          attention.
        </p>
        <a
          href={study.responses.proposed.path}
          target="_blank"
          rel="noreferrer"
        >
          Inspect the recorded result{" "}
          <ArrowUpRight size={16} aria-hidden="true" />
        </a>
      </div>
    </aside>
  );
}
