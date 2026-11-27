import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Health, ModelInfo } from "../api/types";

export interface ModelState {
  loading: boolean;
  health: Health | null;
  info: ModelInfo | null;
  errors: ApiError[];
}
export type Readiness =
  | "loading"
  | "offline"
  | "error"
  | "unavailable"
  | "ready";
export function readiness(s: ModelState): Readiness {
  if (s.loading) return "loading";
  if (s.errors.some((e) => e.kind === "network")) return "offline";
  if (
    s.health?.model_loaded === false ||
    s.info?.ready === false ||
    s.errors.some((e) => e.code === "model_unavailable")
  )
    return "unavailable";
  if (s.errors.length || !s.health || !s.info) return "error";
  return "ready";
}
export function useModelStatus() {
  const [state, setState] = useState<ModelState>({
    loading: true,
    health: null,
    info: null,
    errors: [],
  });
  const active = useRef<AbortController | null>(null);
  const refresh = useCallback(async () => {
    active.current?.abort();
    const controller = new AbortController();
    active.current = controller;
    setState({ loading: true, health: null, info: null, errors: [] });
    const results = await Promise.allSettled([
      api.health(controller.signal),
      api.modelInfo(controller.signal),
    ]);
    if (controller.signal.aborted) return;
    setState({
      loading: false,
      health: results[0].status === "fulfilled" ? results[0].value : null,
      info: results[1].status === "fulfilled" ? results[1].value : null,
      errors: results.flatMap((r) =>
        r.status === "rejected"
          ? [
              r.reason instanceof ApiError
                ? r.reason
                : new ApiError(
                    "Unexpected API error.",
                    null,
                    null,
                    null,
                    "invalid",
                  ),
            ]
          : [],
      ),
    });
  }, []);
  useEffect(() => {
    void refresh();
    return () => active.current?.abort();
  }, [refresh]);
  return { ...state, readiness: readiness(state), refresh };
}
