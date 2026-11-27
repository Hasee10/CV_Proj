import type { CaptureState } from "../../hooks/useSavedCapture";
import type { CaptureRecord, FieldResult } from "../../api/results";
import { sameCapturedInput } from "../../lib/presentation";
import { FieldResultCard } from "./ResultDetails";

export function RecognitionComparison({
  capture,
  record,
  current,
  fresh,
}: {
  capture: CaptureState;
  record: CaptureRecord;
  current: FieldResult;
  fresh: boolean;
}) {
  const baseline = capture.manifest?.records.find(
    (r) => r.id === "numeric-baseline",
  );
  const proposed = capture.manifest?.records.find(
    (r) => r.id === "numeric-proposed",
  );
  const comparable =
    record.id.startsWith("numeric-") && sameCapturedInput(baseline, proposed);
  return (
    <>
      <div className="panel-heading">
        <h2>Recognised field</h2>
        <span className="capture-chip">
          {comparable ? "Identical saved input" : "Single field"}
        </span>
      </div>
      {comparable ? (
        <>
          <div className="method-comparison">
            {(["baseline", "proposed"] as const).map((mode) => {
              const id = `numeric-${mode}`;
              const isCurrent = record.id === id;
              const response = isCurrent
                ? current
                : (capture.responses[id] as FieldResult);
              return (
                <div key={id}>
                  <p className="response-origin">
                    {isCurrent && fresh
                      ? "Fresh live response"
                      : "Saved API capture"}
                  </p>
                  <FieldResultCard
                    compact
                    title={mode === "baseline" ? "Baseline" : "ATHN"}
                    result={response}
                  />
                </div>
              );
            })}
          </div>
          <p className="comparison-note">
            One synthetic DEV crop, byte-identical across both saved requests.
            This example illustrates a difference; it does not establish general
            accuracy.
          </p>
        </>
      ) : (
        <FieldResultCard
          compact
          title={
            current.field_type === "written"
              ? "Written amount"
              : "Numeric amount"
          }
          result={current}
        />
      )}
    </>
  );
}

export function RecognitionPipeline() {
  return (
    <section
      className="polish-card recognition-pipeline"
      aria-label="Explanatory recognition pipeline"
    >
      <div className="panel-heading">
        <h2>How the reading is produced</h2>
        <span>Explanatory diagram</span>
      </div>
      <ol>
        {[
          ["Input", "Original crop"],
          ["Preprocessing", "Identity or ATHN"],
          ["LoGo-HTR", "Same frozen weights"],
          ["Amount parsing", "Decimal string or null"],
        ].map(([title, detail]) => (
          <li key={title}>
            <strong>{title}</strong>
            <span>{detail}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
