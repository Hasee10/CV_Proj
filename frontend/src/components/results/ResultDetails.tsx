import type {
  FieldResult,
  CaptureRecord,
  CaptureManifest,
} from "../../api/results";
import { formatJson } from "../../hooks/useSavedCapture";
export function FieldResultCard({
  result,
  title,
}: {
  result: FieldResult;
  title: string;
}) {
  return (
    <article className="field-result-card">
      <div className="result-card-title">
        <h3>{title}</h3>
        <span className="capture-chip">{result.mode}</span>
      </div>
      <p className="result-label">Raw model text</p>
      <pre className="raw-output">
        {result.raw_text === "" ? (
          <span className="empty-output">(empty output)</span>
        ) : (
          result.raw_text
        )}
      </pre>
      <dl className="parsed-values">
        <div>
          <dt>Parsed value</dt>
          <dd>{result.parsed_value ?? "Not parsed"}</dd>
        </div>
        <div>
          <dt>Parse status</dt>
          <dd>{result.parse_status}</dd>
        </div>
      </dl>
      <div className="latency-grid">
        {Object.entries(result.latency_seconds).map(([key, value]) => (
          <div key={key}>
            <span>{key.replace("_", " ")}</span>
            <strong>{String(value)} s</strong>
          </div>
        ))}
      </div>
      <details className="response-detail">
        <summary>Preprocessing & model details</summary>
        <p>Model score (uncalibrated): {String(result.beam_log_probability)}</p>
        <p>Input shape: {JSON.stringify(result.model_input_shape)}</p>
        {result.image && (
          <p>
            Image: {result.image.width} × {result.image.height} px
          </p>
        )}
        <pre>{formatJson(result.preprocessing)}</pre>
      </details>
    </article>
  );
}
export function CaptureProvenance({
  record,
  manifest,
}: {
  record: CaptureRecord;
  manifest: CaptureManifest;
}) {
  return (
    <details className="capture-provenance">
      <summary>Capture provenance & original JSON</summary>
      <dl>
        <dt>Saved request</dt>
        <dd>
          {record.method} {record.endpoint} · HTTP {record.http_status}
        </dd>
        <dt>Captured (UTC)</dt>
        <dd>{record.captured_at}</dd>
        <dt>Request ID</dt>
        <dd>
          <code>{record.request_id}</code>
        </dd>
        <dt>Checkpoint SHA-256</dt>
        <dd>
          <code>{manifest.checkpoint_sha256}</code>
        </dd>
        <dt>Response SHA-256</dt>
        <dd>
          <code>{record.response_sha256}</code>
        </dd>
        {record.image_sha256 && (
          <>
            <dt>Input image SHA-256</dt>
            <dd>
              <code>{record.image_sha256}</code>
            </dd>
          </>
        )}
        {record.licences && (
          <>
            <dt>Source licences</dt>
            <dd>{record.licences.join("; ")}</dd>
          </>
        )}
      </dl>
      <a href={record.response} download>
        Download the original saved JSON
      </a>
    </details>
  );
}
