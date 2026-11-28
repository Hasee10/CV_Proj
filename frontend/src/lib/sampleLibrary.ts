import { sampleStudies } from "../generated/sampleStudies";
import { workspaceSamples } from "../generated/workspaceSamples";
import type { FieldResult } from "../api/results";

export interface LabSample {
  id: string;
  title: string;
  field_type: "numeric" | "written";
  synthetic: boolean;
  split: "dev";
  image: string;
  source_id: string;
  responses: Record<
    "baseline" | "proposed",
    { path: string; sha256: string; result: FieldResult }
  >;
}
export const labSamples: LabSample[] = [
  ...workspaceSamples,
  ...sampleStudies.map((s) => ({
    ...s,
    field_type: "numeric",
    title:
      s.id === "digits"
        ? "Digit string / CVL 01"
        : s.id === "handwriting"
          ? "Handwritten field / GNHK"
          : "Numeric field / Synthetic 01",
  })),
] as unknown as LabSample[];
