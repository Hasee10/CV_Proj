import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  isBenchmarkResult,
  isFieldResult,
  isVerifyResult,
} from "../api/results";
import type { CaptureManifest, JsonValue } from "../api/results";
export interface CaptureState {
  loading: boolean;
  manifest: CaptureManifest | null;
  responses: Record<string, unknown>;
  error: string | null;
}
async function readJson(path: string, signal: AbortSignal): Promise<unknown> {
  if (!path.startsWith("/results/") || path.includes(".."))
    throw new Error("Invalid saved response path.");
  const response = await fetch(path, { signal, cache: "no-store" });
  if (!response.ok)
    throw new Error(`Saved capture unavailable (HTTP ${response.status}).`);
  return response.json();
}
export function useSavedCapture(): CaptureState {
  const [state, setState] = useState<CaptureState>({
    loading: true,
    manifest: null,
    responses: {},
    error: null,
  });
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      try {
        const latest = (await readJson(
          "/results/latest.json",
          controller.signal,
        )) as { manifest: string };
        if (typeof latest.manifest !== "string")
          throw new Error("Invalid capture index.");
        const manifest = (await readJson(
          latest.manifest,
          controller.signal,
        )) as CaptureManifest;
        if (
          typeof manifest.run_id !== "string" ||
          !Array.isArray(manifest.records)
        )
          throw new Error("Invalid capture manifest.");
        const pairs = await Promise.all(
          manifest.records.map(async (record) => {
            const result = await readJson(record.response, controller.signal);
            if (record.kind === "verification" && !isVerifyResult(result))
              throw new Error("Invalid saved verification response.");
            if (record.kind === "recognition" && !isFieldResult(result))
              throw new Error("Invalid saved recognition response.");
            if (record.kind === "saved_research" && !isBenchmarkResult(result))
              throw new Error("Invalid saved benchmark response.");
            return [record.id, result] as const;
          }),
        );
        if (!controller.signal.aborted)
          setState({
            loading: false,
            manifest,
            responses: Object.fromEntries(pairs),
            error: null,
          });
      } catch (e) {
        if (!controller.signal.aborted)
          setState({
            loading: false,
            manifest: null,
            responses: {},
            error:
              e instanceof Error ? e.message : "Unable to load saved results.",
          });
      }
    })();
    return () => controller.abort();
  }, []);
  return state;
}
export function useCaptureContext() {
  return useOutletContext<{ capture: CaptureState }>().capture;
}
export function formatJson(value: unknown) {
  return JSON.stringify(value as JsonValue, null, 2);
}
