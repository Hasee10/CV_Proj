import { useSyncExternalStore } from "react";
import {
  isFieldResult,
  isVerifyResult,
  type FieldResult,
  type VerifyResult,
} from "../api/results";

export interface SessionRun {
  id: string;
  at: string;
  source: string;
  kind: "recognition" | "verification";
  result: FieldResult | VerifyResult;
}
const key = "chequeverify.session.v1";
const empty: SessionRun[] = [];
let cache: SessionRun[] | undefined;
const listeners = new Set<() => void>();
function read() {
  if (cache) return cache;
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(key) || "[]");
    cache = Array.isArray(value)
      ? value
          .filter(
            (r): r is SessionRun =>
              typeof r?.id === "string" &&
              typeof r.at === "string" &&
              typeof r.source === "string" &&
              ((r.kind === "recognition" && isFieldResult(r.result)) ||
                (r.kind === "verification" && isVerifyResult(r.result))),
          )
          .slice(0, 50)
      : [];
  } catch {
    cache = [];
  }
  return cache;
}
function publish(runs: SessionRun[]) {
  cache = runs;
  try {
    sessionStorage.setItem(key, JSON.stringify(runs));
  } catch {
    /* In-memory session still works. */
  }
  listeners.forEach((listener) => listener());
}
export function recordRun(
  kind: SessionRun["kind"],
  source: string,
  result: SessionRun["result"],
) {
  publish(
    [
      {
        id: crypto.randomUUID(),
        at: new Date().toISOString(),
        kind,
        source,
        result,
      },
      ...read(),
    ].slice(0, 50),
  );
}
export function clearRuns() {
  publish([]);
}
export function useSessionRuns() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    read,
    () => empty,
  );
}
export function sessionStats(runs: SessionRun[]) {
  const fields = runs.flatMap((r) =>
    "decision" in r.result ? [r.result.numeric, r.result.written] : [r.result],
  );
  const seconds = runs.map((r) =>
    "decision" in r.result
      ? r.result.total_latency_seconds
      : r.result.latency_seconds.total,
  );
  return {
    requests: runs.length,
    fields: fields.length,
    parsed: fields.filter((f) => f.parsed_value !== null).length,
    review: runs.filter(
      (r) => "decision" in r.result && r.result.decision === "review",
    ).length,
    meanSeconds: seconds.length
      ? seconds.reduce((a, b) => a + b, 0) / seconds.length
      : null,
  };
}
