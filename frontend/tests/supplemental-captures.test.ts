import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { sampleStudies } from "../src/generated/sampleStudies";
import { isFieldResult } from "../src/api/results";

const bytes = (path: string) =>
  readFileSync(new URL("../public" + path, import.meta.url));
const sha = (data: Buffer) => createHash("sha256").update(data).digest("hex");

describe("Supplemental DEV examples", () => {
  it("preserves exact API responses and source images for every displayed sample", () => {
    expect(sampleStudies).toHaveLength(3);
    for (const study of sampleStudies) {
      expect(study.split).toBe("dev");
      expect(sha(bytes(study.image))).toBe(study.image_sha256);
      for (const mode of ["baseline", "proposed"] as const) {
        const capture = study.responses[mode];
        const raw = bytes(capture.path);
        expect(sha(raw)).toBe(capture.sha256);
        expect(JSON.parse(raw.toString())).toEqual(capture.result);
        expect(isFieldResult(capture.result)).toBe(true);
      }
    }
  });
  it("retains failed and unchanged readings alongside improvements", () => {
    expect(sampleStudies[0].responses.baseline.result.raw_text).toBe("135529");
    expect(sampleStudies[0].responses.proposed.result.raw_text).toBe("135529");
    expect(sampleStudies[1].responses.baseline.result.parsed_value).toBeNull();
    expect(sampleStudies[2].responses.baseline.result.parsed_value).toBeNull();
  });
});
