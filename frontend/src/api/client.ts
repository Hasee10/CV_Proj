import type { BackendError, Health, ModelInfo } from "./types";
import { isBenchmarkResult, isFieldResult, isVerifyResult } from "./results";

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number | null,
    public code: string | null = null,
    public requestId: string | null = null,
    public kind: "http" | "network" | "invalid" = "http",
  ) {
    super(message);
    this.name = "ApiError";
  }
}
const object = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const strings = (v: unknown): v is string[] =>
  Array.isArray(v) && v.every((x) => typeof x === "string");
export const isHealth = (v: unknown): v is Health =>
  object(v) &&
  ((v.status === "ok" && v.model_loaded === true) ||
    (v.status === "model_unavailable" && v.model_loaded === false));
export function isModelInfo(v: unknown): v is ModelInfo {
  if (
    !object(v) ||
    ![
      "model",
      "checkpoint_sha256",
      "upstream_commit",
      "dictionary",
      "preprocessing",
      "decoding",
      "device",
    ].every((k) => typeof v[k] === "string") ||
    !(
      v.parameter_count === null ||
      (typeof v.parameter_count === "number" &&
        Number.isFinite(v.parameter_count))
    ) ||
    typeof v.ready !== "boolean" ||
    !["baseline", "proposed"].includes(String(v.default_mode)) ||
    !strings(v.limitations) ||
    !object(v.modes)
  )
    return false;
  const p = v.modes.proposed;
  if (
    typeof v.modes.baseline !== "string" ||
    !object(p) ||
    typeof p.method !== "string" ||
    !(p.status === null || typeof p.status === "string")
  )
    return false;
  const c = p.config;
  return (
    c === null ||
    (object(c) &&
      typeof c.id === "string" &&
      typeof c.method === "string" &&
      ["band_lo", "band_hi", "target", "min_scale", "max_scale"].every(
        (k) => typeof c[k] === "number" && Number.isFinite(c[k]),
      ))
  );
}
function backendError(v: unknown): BackendError | null {
  if (!object(v) || !object(v.error)) return null;
  const e = v.error;
  return typeof e.code === "string" &&
    typeof e.message === "string" &&
    typeof e.request_id === "string"
    ? (e as unknown as BackendError)
    : null;
}
export function createApiClient(
  baseUrl = API_BASE_URL,
  fetcher: typeof fetch = fetch,
) {
  async function get<T>(
    path: string,
    validate: (v: unknown) => v is T,
    signal?: AbortSignal,
    health = false,
    init: RequestInit = {},
  ): Promise<T> {
    let response: Response;
    try {
      response = await fetcher(`${baseUrl.replace(/\/+$/, "")}${path}`, {
        ...init,
        signal,
        headers: { Accept: "application/json" },
      });
    } catch (e) {
      if (signal?.aborted || (e instanceof Error && e.name === "AbortError"))
        throw e;
      throw new ApiError(
        `Backend unreachable at ${baseUrl}. Check the server and CORS configuration.`,
        null,
        null,
        null,
        "network",
      );
    }
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      throw new ApiError(
        `Unexpected non-JSON response (HTTP ${response.status}).`,
        response.status,
        null,
        response.headers.get("X-Request-ID"),
        "invalid",
      );
    }
    // Health's 503 is a valid readiness response, not the standard error envelope.
    if (
      health &&
      response.status === 503 &&
      isHealth(body) &&
      !body.model_loaded
    )
      return body as T;
    if (!response.ok) {
      const e = backendError(body);
      throw new ApiError(
        e?.message ?? `Unexpected API response (HTTP ${response.status}).`,
        response.status,
        e?.code ?? null,
        e?.request_id ?? response.headers.get("X-Request-ID"),
      );
    }
    if (!validate(body))
      throw new ApiError(
        `Unexpected response format from ${path} (HTTP ${response.status}).`,
        response.status,
        null,
        response.headers.get("X-Request-ID"),
        "invalid",
      );
    return body;
  }
  return {
    health: (signal?: AbortSignal) => get("/health", isHealth, signal, true),
    modelInfo: (signal?: AbortSignal) =>
      get("/api/model-info", isModelInfo, signal),
    benchmark: (signal?: AbortSignal) =>
      get("/api/benchmark", isBenchmarkResult, signal),
    verify: (body: FormData, signal?: AbortSignal) =>
      get("/api/verify", isVerifyResult, signal, false, {
        method: "POST",
        body,
      }),
    recognize: (body: FormData, signal?: AbortSignal) =>
      get("/api/recognize", isFieldResult, signal, false, {
        method: "POST",
        body,
      }),
  };
}
export const api = createApiClient();
