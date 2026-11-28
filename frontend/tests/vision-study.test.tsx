import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { WorkflowSection } from "../src/components/visuals/LandingStudy";
import {
  ScaleDiagram,
  VisionSpecimen,
} from "../src/components/visuals/VisionSpecimen";
import {
  CerSculpture,
  ResearchEvidence,
  researchDatasets,
} from "../src/components/visuals/ResearchEvidence";
import type {
  BenchmarkResult,
  CaptureManifest,
  FieldResult,
} from "../src/api/results";
import type { CaptureState } from "../src/hooks/useSavedCapture";

const asset = (path: string) => new URL("../public" + path, import.meta.url);
const read = (path: string) => JSON.parse(readFileSync(asset(path), "utf8"));
const manifest = read(read("/results/latest.json").manifest) as CaptureManifest;
const responses = Object.fromEntries(
  manifest.records.map((r) => [r.id, read(r.response)]),
);
const capture = {
  loading: false,
  error: null,
  manifest,
  responses,
} as CaptureState;
const data = responses.benchmark as BenchmarkResult;
const baseline = responses["numeric-baseline"] as FieldResult,
  proposed = responses["numeric-proposed"] as FieldResult;

describe("CV landing studies use recorded evidence", () => {
  it("traces a full recorded pair through both raw readings and parsed values", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <WorkflowSection capture={capture} />
      </MemoryRouter>,
    );
    expect(html).toContain("Keep the pixels.");
    expect(html).toContain("Make the reading explicit.");
    expect(html).toContain("Amounts agree");
    expect(html).toContain("1.00");
    expect(html).toContain("one");
    expect(html).toContain("Genuine handwriting");
    expect(html).toContain("Constructed DEV pair");
    expect(html).toContain("/verify?example=sheet_accept");
    expect(html).toContain(responses.sheet_accept.request_id);
    expect(html).toContain("/workflow/input-tile.png");
    expect(html).toContain("/workflow/comparison-hub.png");
  });
  it("distinguishes prepared image dimensions from estimated text height and target", () => {
    const html = renderToStaticMarkup(
      <ScaleDiagram
        baseline={baseline}
        proposed={proposed}
        targetHeight={Number(data.proposed_config.target)}
      />,
    );
    expect(html).toContain("baseline 133 by 40 pixels; ATHN 404 by 122 pixels");
    expect(html).toContain("3.038");
    expect(html).toContain("15.8");
    expect(html).toContain("48");
    expect(html).toContain("not a processed-image preview");
  });
  it.each(researchDatasets)(
    "retains both exact CER labels for $title",
    (definition) => {
      const metrics = data.datasets[definition.id];
      const html = renderToStaticMarkup(
        <CerSculpture
          metrics={metrics}
          title={definition.title}
          synthetic={definition.domain === "synthetic"}
        />,
      );
      for (const value of [metrics.cer.baseline, metrics.cer.proposed])
        expect(html).toContain((value * 100).toFixed(2) + "%");
      if (definition.domain === "synthetic")
        expect(html).toContain("Axis zero to 110.00%");
      expect(html).toContain("front-face heights");
    },
  );
  it("keeps the baseline and ATHN raw values and decimal strings separate", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <VisionSpecimen capture={capture} />
      </MemoryRouter>,
    );
    expect(html).toContain("7.00");
    expect(html).toContain("Not parsed");
    expect(html).toContain("Handwritten field");
    expect(html).toContain("Digit string");
    expect(html).toContain("Synthetic field");
    expect(html).toContain("Same frozen LoGo-HTR");
    expect(html).toContain("not model attention");
    expect(html).toContain("not an accuracy claim");
    expect(html).not.toContain("confidence score");
  });
  it("exposes all six datasets, the regression, and both synthetic limitations", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <ResearchEvidence capture={capture} />
      </MemoryRouter>,
    );
    for (const definition of researchDatasets)
      expect(html).toContain(definition.title);
    expect(html).toContain("CER increased");
    expect(html).toContain("164");
    expect(html).toContain("87");
    expect(html).toContain("not statistically significant");
    expect(html).toContain("No real handwritten cheques");
  });
  it("exports the same scientific diagrams as self-contained SVGs", () => {
    for (const definition of researchDatasets) {
      const svg = readFileSync(
        asset(`/study/cer-${definition.id}.svg`),
        "utf8",
      );
      expect(svg).toContain('xmlns="http://www.w3.org/2000/svg"');
      expect(svg).toContain(
        (data.datasets[definition.id].cer.proposed * 100).toFixed(2) + "%",
      );
      expect(svg).not.toContain("<script");
    }
    expect(readFileSync(asset("/study/athn-scale.svg"), "utf8")).toContain(
      "baseline 133 by 40 pixels; ATHN 404 by 122 pixels",
    );
  });
});
