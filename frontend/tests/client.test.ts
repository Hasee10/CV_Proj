import { describe, expect, it, vi } from "vitest";
import { ApiError, createApiClient, isModelInfo } from "../src/api/client";
import { readiness } from "../src/hooks/useModelStatus";
import example from "../../artifacts/M10/examples/model_info.json";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": "header-id",
    },
  });
const clientFor = (response: Response) =>
  createApiClient(
    "http://localhost:8000/",
    vi.fn<typeof fetch>().mockResolvedValue(response),
  );
describe("F1 API contract", () => {
  it("accepts the actual saved model-info shape", async () => {
    expect(await clientFor(json(example.response)).modelInfo()).toEqual(
      example.response,
    );
  });
  it("accepts health 503 as a model-unavailable state", async () => {
    expect(
      await clientFor(
        json({ status: "model_unavailable", model_loaded: false }, 503),
      ).health(),
    ).toEqual({ status: "model_unavailable", model_loaded: false });
  });
  it("validates successful health bodies", async () => {
    await expect(
      clientFor(json({ status: "ok", model_loaded: false })).health(),
    ).rejects.toMatchObject({ kind: "invalid" });
  });
  it.each([
    ["busy", 503],
    ["model_unavailable", 503],
    ["inference_timeout", 504],
    ["file_too_large", 413],
    ["unsupported_media_type", 415],
    ["invalid_request", 422],
    ["internal_error", 500],
  ])("preserves %s errors", async (code, status) => {
    await expect(
      clientFor(
        json(
          {
            error: {
              code,
              message: "Exact backend message",
              request_id: "body-id",
            },
          },
          status as number,
        ),
      ).modelInfo(),
    ).rejects.toMatchObject({
      code,
      status,
      message: "Exact backend message",
      requestId: "body-id",
    });
  });
  it("handles non-JSON errors with HTTP status and header request ID", async () => {
    await expect(
      clientFor(
        new Response("<html>Failure</html>", {
          status: 502,
          headers: { "X-Request-ID": "proxy-id" },
        }),
      ).health(),
    ).rejects.toMatchObject({
      kind: "invalid",
      status: 502,
      requestId: "proxy-id",
    });
  });
  it("handles unknown JSON errors without inventing a code", async () => {
    await expect(
      clientFor(json({ detail: "Not Found" }, 404)).health(),
    ).rejects.toMatchObject({
      status: 404,
      code: null,
      requestId: "header-id",
    });
  });
  it("rejects malformed success and partial model-info", async () => {
    await expect(
      clientFor(json({ ...example.response, modes: {} })).modelInfo(),
    ).rejects.toMatchObject({ kind: "invalid" });
  });
  it("reports network failures", async () => {
    const api = createApiClient(
      "http://localhost:8000",
      vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    await expect(api.health()).rejects.toMatchObject({
      kind: "network",
      status: null,
    });
  });
  it("forwards the abort signal and preserves cancellation", async () => {
    const controller = new AbortController();
    controller.abort();
    const error = new DOMException("Aborted", "AbortError");
    const mock = vi.fn<typeof fetch>().mockRejectedValue(error);
    await expect(
      createApiClient("http://localhost:8000/", mock).health(controller.signal),
    ).rejects.toBe(error);
    expect(mock).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({ signal: controller.signal }),
    );
  });
});
describe("dashboard readiness", () => {
  if (!isModelInfo(example.response))
    throw new Error("Saved model-info does not match the API contract");
  const ready = {
    loading: false,
    health: { status: "ok" as const, model_loaded: true },
    info: example.response,
    errors: [],
  };
  it("distinguishes loading, ready, unavailable, offline, and unexpected errors", () => {
    expect(readiness(ready)).toBe("ready");
    expect(readiness({ ...ready, loading: true })).toBe("loading");
    expect(
      readiness({
        ...ready,
        health: { status: "model_unavailable", model_loaded: false },
      }),
    ).toBe("unavailable");
    expect(readiness({ ...ready, info: { ...ready.info, ready: false } })).toBe(
      "unavailable",
    );
    expect(
      readiness({
        ...ready,
        errors: [new ApiError("offline", null, null, null, "network")],
      }),
    ).toBe("offline");
    expect(
      readiness({ ...ready, info: null, errors: [new ApiError("bad", 500)] }),
    ).toBe("error");
  });
});
