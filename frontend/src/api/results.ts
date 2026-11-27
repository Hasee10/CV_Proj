import type { Mode } from "./types";
export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };
export interface FieldResult {
  field_type: "numeric" | "written";
  mode: Mode;
  raw_text: string;
  parsed_value: string | null;
  parse_status: "parsed" | "unparseable";
  beam_log_probability: number;
  preprocessing: Record<string, JsonValue>;
  model_input_shape: number[];
  latency_seconds: {
    preprocess: number;
    queue_wait: number;
    inference: number;
    total: number;
  };
  request_id?: string;
  image?: { width: number; height: number };
}
export interface VerifyResult {
  decision: "accept" | "flag" | "review";
  reasons: string[];
  notice: string;
  request_id: string;
  mode: Mode;
  numeric: FieldResult;
  written: FieldResult;
  rois: { numeric_px: number[]; written_px: number[] } | null;
  total_latency_seconds: number;
}
export interface DatasetMetrics {
  n_eligible: number;
  cer: { baseline: number; proposed: number; delta: number };
  wer: { baseline: number; proposed: number; delta: number };
  exact: { baseline: number; proposed: number };
  exact_rate: { baseline: number; proposed: number; delta_pp: number };
  value_exact?: {
    baseline: number;
    proposed: number;
    n: number;
    delta_pp: number;
    parseable?: { baseline: number; proposed: number };
  };
}
export interface PairMetrics {
  n_eligible: number;
  unresolved: number;
  decisions: Partial<Record<"accept" | "flag" | "review", number>>;
  review_rate: number;
  decision_coverage: number;
  incorrect_acceptance_rate: number;
  incorrect_rejection_rate: number | null;
  explicit_mismatch_detection: number;
  auto_accepted_matches: number;
  confusion: Record<string, number>;
}
export interface BenchmarkResult {
  source: string;
  split: string;
  datasets: Record<string, DatasetMetrics>;
  pairs: Record<string, { baseline: PairMetrics; proposed: PairMetrics }>;
  proposed_config: Record<string, JsonValue>;
}
export interface CaptureRecord {
  id: string;
  endpoint: string;
  method: string;
  captured_at: string;
  http_status: number;
  request_id: string;
  response: string;
  response_sha256: string;
  image?: string;
  image_sha256?: string;
  source_path?: string;
  fields?: Record<string, string>;
  kind?: "verification" | "recognition" | "saved_research";
  description?: string;
  split?: string;
  constructed?: boolean;
  synthetic?: boolean;
  licences?: string[];
}
export interface CaptureManifest {
  run_id: string;
  captured_at: string;
  base_url: string;
  source_git_commit: string;
  checkpoint_sha256: string;
  upstream_commit: string;
  notice: string;
  records: CaptureRecord[];
}
const obj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const numeric = (v: unknown): v is number =>
  typeof v === "number" && Number.isFinite(v);
export function isFieldResult(v: unknown): v is FieldResult {
  return (
    obj(v) &&
    ["numeric", "written"].includes(String(v.field_type)) &&
    ["baseline", "proposed"].includes(String(v.mode)) &&
    typeof v.raw_text === "string" &&
    (v.parsed_value === null || typeof v.parsed_value === "string") &&
    ["parsed", "unparseable"].includes(String(v.parse_status)) &&
    numeric(v.beam_log_probability) &&
    obj(v.preprocessing) &&
    Array.isArray(v.model_input_shape) &&
    v.model_input_shape.every(numeric) &&
    obj(v.latency_seconds) &&
    ["preprocess", "queue_wait", "inference", "total"].every((k) =>
      numeric((v.latency_seconds as Record<string, unknown>)[k]),
    )
  );
}
export function isVerifyResult(v: unknown): v is VerifyResult {
  return (
    obj(v) &&
    ["accept", "flag", "review"].includes(String(v.decision)) &&
    typeof v.notice === "string" &&
    typeof v.request_id === "string" &&
    ["baseline", "proposed"].includes(String(v.mode)) &&
    Array.isArray(v.reasons) &&
    v.reasons.every((x) => typeof x === "string") &&
    isFieldResult(v.numeric) &&
    isFieldResult(v.written) &&
    numeric(v.total_latency_seconds) &&
    (v.rois === null ||
      (obj(v.rois) &&
        ["numeric_px", "written_px"].every(
          (k) =>
            Array.isArray((v.rois as Record<string, unknown>)[k]) &&
            ((v.rois as Record<string, unknown>)[k] as unknown[]).length ===
              4 &&
            ((v.rois as Record<string, unknown>)[k] as unknown[]).every(
              numeric,
            ),
        )))
  );
}
export function isBenchmarkResult(v: unknown): v is BenchmarkResult {
  if (
    !obj(v) ||
    typeof v.source !== "string" ||
    typeof v.split !== "string" ||
    !obj(v.datasets) ||
    !obj(v.pairs) ||
    !obj(v.proposed_config)
  )
    return false;
  return (
    Object.values(v.datasets).every(
      (d) =>
        obj(d) &&
        numeric(d.n_eligible) &&
        obj(d.cer) &&
        numeric(d.cer.baseline) &&
        numeric(d.cer.proposed) &&
        obj(d.wer) &&
        obj(d.exact) &&
        obj(d.exact_rate),
    ) &&
    Object.values(v.pairs).every(
      (p) =>
        obj(p) &&
        ["baseline", "proposed"].every(
          (m) =>
            obj(p[m]) &&
            numeric(p[m].n_eligible) &&
            obj(p[m].decisions) &&
            obj(p[m].confusion),
        ),
    )
  );
}
