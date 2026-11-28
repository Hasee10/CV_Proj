/** Export the very same SVG components used on the landing page.
 * Run from frontend/: node scripts/create-study-svg.mjs
 * Reads stored captures only. No requests, inference, or metric recomputation.
 */
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import type { ReactElement } from "react";
import { ScaleDiagram } from "../src/components/visuals/VisionSpecimen";
import {
  CerSculpture,
  researchDatasets,
} from "../src/components/visuals/ResearchEvidence";
import type {
  BenchmarkResult,
  CaptureManifest,
  FieldResult,
} from "../src/api/results";

const publicDir = new URL("../public/", import.meta.url);
const read = (path: string) =>
  JSON.parse(readFileSync(new URL(path.replace(/^\//, ""), publicDir), "utf8"));
const manifest = read(read("results/latest.json").manifest) as CaptureManifest;
const response = (id: string) =>
  read(manifest.records.find((r) => r.id === id)!.response);
const benchmark = response("benchmark") as BenchmarkResult;
const output = new URL("study/", publicDir);
mkdirSync(output, { recursive: true });
function save(name: string, element: ReactElement) {
  const svg = renderToStaticMarkup(element).replace(
    /(<svg[^>]*>)/,
    '$1<rect width="100%" height="100%" fill="#183c31"/>',
  );
  writeFileSync(
    new URL(name, output),
    '<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n",
  );
}
save(
  "athn-scale.svg",
  <ScaleDiagram
    baseline={response("numeric-baseline") as FieldResult}
    proposed={response("numeric-proposed") as FieldResult}
    targetHeight={Number(benchmark.proposed_config.target)}
  />,
);
for (const definition of researchDatasets)
  save(
    `cer-${definition.id}.svg`,
    <CerSculpture
      metrics={benchmark.datasets[definition.id]}
      title={definition.title}
      synthetic={definition.domain === "synthetic"}
    />,
  );
writeFileSync(
  new URL("provenance.json", output),
  JSON.stringify(
    {
      capture_run: manifest.run_id,
      source: "saved API responses",
      numerical_metrics: "unchanged",
      generated_by: "frontend/scripts/create-study-svg.tsx",
      files: 7,
    },
    null,
    2,
  ) + "\n",
);
process.stdout.write(`Exported 7 SVG studies to ${fileURLToPath(output)}\n`);
