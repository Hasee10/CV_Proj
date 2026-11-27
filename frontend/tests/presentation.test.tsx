import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import {
  automaticDecisions,
  decisionCounts,
  percent,
  roiRect,
  sameCapturedInput,
} from "../src/lib/presentation";
import { RecognitionComparison } from "../src/components/results/RecognitionComparison";
import { BenchmarkVisuals } from "../src/components/research/BenchmarkVisuals";
import type { CaptureManifest, BenchmarkResult } from "../src/api/results";
import type { CaptureState } from "../src/hooks/useSavedCapture";

const read = (path: string) =>
  JSON.parse(
    readFileSync(new URL("../public" + path, import.meta.url), "utf8"),
  );
const manifest = read(read("/results/latest.json").manifest) as CaptureManifest;
const responses = Object.fromEntries(
  manifest.records.map((r) => [r.id, read(r.response)]),
);
const capture = {
  manifest,
  responses,
  error: null,
  loading: false,
} as CaptureState;
const data = responses.benchmark as BenchmarkResult;
describe("Evidence presentation preserves backend meaning", () => {
  it("maps exact pixel coordinates without rounding, including fractional ROIs", () => {
    expect(roiRect([845, 40, 860, 66])).toEqual({
      x: 845,
      y: 40,
      width: 15,
      height: 26,
    });
    expect(roiRect([0.25, 1.5, 9.75, 11.25])).toEqual({
      x: 0.25,
      y: 1.5,
      width: 9.5,
      height: 9.75,
    });
  });
  it("rejects degenerate or nonfinite regions instead of drawing incorrect overlays", () => {
    for (const box of [
      [0, 0, 0, 4],
      [5, 0, 1, 4],
      [0, 0, 4],
      [0, 0, NaN, 4],
    ])
      expect(() => roiRect(box)).toThrow("Invalid pixel ROI");
  });
  it("uses image identity rather than example name or path for comparison", () => {
    const baseline = manifest.records.find((r) => r.id === "numeric-baseline")!;
    const proposed = manifest.records.find((r) => r.id === "numeric-proposed")!;
    expect(sameCapturedInput(baseline, proposed)).toBe(true);
    expect(
      sameCapturedInput(baseline, { ...proposed, image_sha256: "different" }),
    ).toBe(false);
    expect(sameCapturedInput(undefined, undefined)).toBe(false);
  });
  it("formats rates above one without clipping and distinguishes null from missing", () => {
    expect(percent(1.0135)).toBe("101.35%");
    expect(percent(0)).toBe("0.00%");
    expect(percent(null)).toBe("n/a");
    expect(percent(undefined)).toBe("Not reported");
  });
  it("keeps unresolved synthetic decisions in the decision count, outside eligible denominators", () => {
    const metrics = data.pairs.syn_all_SYNTHETIC.proposed;
    expect(decisionCounts(metrics)).toEqual([
      { key: "accept", count: 0 },
      { key: "flag", count: 0 },
      { key: "review", count: 164 },
    ]);
    expect(metrics.n_eligible).toBe(146);
    expect(metrics.unresolved).toBe(18);
    expect(
      automaticDecisions(data.pairs.gnhk_pairs_genuine_constructed.baseline),
    ).toBe(24);
    expect(
      automaticDecisions(data.pairs.gnhk_pairs_genuine_constructed.proposed),
    ).toBe(27);
  });
  it("maps each method to its actual raw reading, decimal value and preprocessing time", () => {
    const record = manifest.records.find((r) => r.id === "numeric-baseline")!;
    const html = renderToStaticMarkup(
      <RecognitionComparison
        capture={capture}
        record={record}
        current={responses[record.id]}
        fresh={false}
      />,
    );
    const baseline = html.slice(html.indexOf("Baseline"), html.indexOf("ATHN"));
    expect(baseline).toContain("3003.00");
    expect(baseline).not.toContain("3083.00");
    expect(html.slice(html.indexOf("ATHN"))).toContain("3083.00");
    expect(html).toContain("0.0513");
    expect(html).toContain("1.036");
  });
  it("renders every dataset and preserves the synthetic zero and unresolved denominator", () => {
    const html = renderToStaticMarkup(<BenchmarkVisuals data={data} />);
    expect(html).toContain("101.35%");
    expect(html).toContain("146");
    expect(html).toContain("18");
    expect(html).toContain("Cheque written");
    expect(html).toContain("87");
    expect(html).toContain("not statistically significant");
    expect(html).toContain("No real handwritten cheques");
  });
});
