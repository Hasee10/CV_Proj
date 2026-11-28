import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { workspaceSamples } from "../src/generated/workspaceSamples";
import { labSamples } from "../src/lib/sampleLibrary";
import { sessionStats, type SessionRun } from "../src/lib/sessionRuns";
import { guideAnswer } from "../src/components/ui/WorkspaceAssistant";
import { LiveLab, validateUpload } from "../src/components/results/LiveLab";
import {
  ConfusionHeatmap,
  DecisionDonut,
  BenchmarkExplorer,
} from "../src/components/research/BenchmarkExplorer";
import type { BenchmarkResult, FieldResult } from "../src/api/results";
const asset = (path: string) => new URL("../public" + path, import.meta.url);
const latest = JSON.parse(readFileSync(asset("/results/latest.json"), "utf8"));
const manifest = JSON.parse(readFileSync(asset(latest.manifest), "utf8"));
const benchmark = JSON.parse(
  readFileSync(
    asset(
      manifest.records.find((r: { id: string }) => r.id === "benchmark")
        .response,
    ),
    "utf8",
  ),
) as BenchmarkResult;
describe("Live workspace", () => {
  it("retains all seven DEV inputs and exact response bytes, including failed parses", () => {
    expect(labSamples).toHaveLength(7);
    for (const sample of workspaceSamples) {
      expect(sample.split).toBe("dev");
      const source = readFileSync(asset(sample.image));
      expect(createHash("sha256").update(source).digest("hex")).toBe(
        sample.image_sha256,
      );
      for (const mode of ["baseline", "proposed"] as const) {
        const record = sample.responses[mode],
          raw = readFileSync(asset(record.path));
        expect(createHash("sha256").update(raw).digest("hex")).toBe(
          record.sha256,
        );
        expect(JSON.parse(raw.toString())).toEqual(record.result);
      }
    }
    expect(
      workspaceSamples[3].responses.proposed.result.parsed_value,
    ).toBeNull();
  });
  it("counts actual requests and fields without claiming accuracy", () => {
    const first = workspaceSamples[0].responses.baseline
      .result as unknown as FieldResult;
    const failed = workspaceSamples[1].responses.baseline
      .result as unknown as FieldResult;
    const runs: SessionRun[] = [first, failed].map((result, i) => ({
      id: String(i),
      at: "2026-11-28",
      source: "DEV",
      kind: "recognition",
      result,
    }));
    const stats = sessionStats(runs);
    expect(stats.requests).toBe(2);
    expect(stats.fields).toBe(2);
    expect(stats.parsed).toBe(1);
    expect(stats.review).toBe(0);
    expect(stats.meanSeconds).toBe(
      (first.latency_seconds.total + failed.latency_seconds.total) / 2,
    );
    expect(sessionStats([]).meanSeconds).toBeNull();
  });
  it("rejects invalid and oversized uploads before inference", () => {
    expect(validateUpload({ type: "image/png", size: 2000 })).toBeNull();
    expect(validateUpload({ type: "text/html", size: 2000 })).toContain(
      "PNG or JPEG",
    );
    expect(
      validateUpload({ type: "image/png", size: 6 * 1024 * 1024 }),
    ).toContain("5 MB");
    expect(validateUpload({ type: "image/png", size: 0 })).toContain("empty");
  });
  it("opens a requested sample with saved responses and an explicit live run action", () => {
    function Layout() {
      return (
        <Outlet
          context={{
            readiness: "ready",
            capture: {
              manifest: null,
              responses: {},
              loading: false,
              error: null,
            },
          }}
        />
      );
    }
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/recognize?sample=synthetic-02"]}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/recognize" element={<LiveLab kind="recognition" />} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(html).toContain("8312.00");
    expect(html).toContain("Ban");
    expect(html).toContain("Recorded API response");
    expect(html).toContain("Run recognition");
    expect(html).toContain("Upload crops");
  });
  it("keeps the local guide honest about its current connection", () => {
    expect(guideAnswer("Groq API key")).toContain("local field guide");
    expect(guideAnswer("Can I detect fraud?")).toContain("does not establish");
    expect(guideAnswer("Why null?")).toContain("stays unresolved");
  });
});
describe("Meaningful benchmark charts", () => {
  it("uses all decision counts in a donut but excludes unresolved cases from the matrix", () => {
    const pair = benchmark.pairs.syn_all_SYNTHETIC.proposed;
    const donut = renderToStaticMarkup(<DecisionDonut metrics={pair} />),
      heatmap = renderToStaticMarkup(<ConfusionHeatmap metrics={pair} />);
    expect(donut).toContain("164 total decisions");
    expect(heatmap).toContain("146");
    expect(heatmap).toContain("18");
    expect(heatmap).toContain("unresolved excluded");
  });
  it("shows actual result labels, metric controls, and research limits", () => {
    const html = renderToStaticMarkup(<BenchmarkExplorer data={benchmark} />);
    expect(html).toContain("Chart measure");
    expect(html).toContain("Word error rate");
    expect(html).toContain("29.60%");
    expect(html).toContain("25.21%");
    expect(html).toContain("101.35%");
    expect(html).toContain("Outcome heatmap");
    expect(html).toContain("not statistically significant");
  });
});
