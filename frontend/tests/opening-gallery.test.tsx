import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { renderToStaticMarkup } from "react-dom/server";
import {
  EntryExperience,
  openingProgress,
  specimenVisibility,
} from "../src/components/visuals/EntryExperience";

const asset = (path: string) => new URL("../public/" + path, import.meta.url);

describe("Evidence-based depth opening", () => {
  it("never paints overlapping specimen text at any scroll position", () => {
    for (let step = 0; step <= 1000; step++) {
      const plate = step / 200;
      for (const reduced of [false, true]) {
        const visible = Array.from({ length: 6 }, (_, i) =>
          specimenVisibility(i, plate, reduced),
        ).filter((v) => v > 0.001);
        expect(visible.length).toBeLessThanOrEqual(1);
      }
    }
    expect(specimenVisibility(0, 0.55)).toBe(0);
    expect(specimenVisibility(1, 0.7)).toBeGreaterThan(0);
    expect(specimenVisibility(5, 5)).toBe(1);
  });
  it("holds the last image before dissolving completely into the site", () => {
    expect(openingProgress(0, 100)).toEqual({
      phase: 0,
      plate: 0,
      dissolve: 0,
    });
    expect(openingProgress(84, 100).plate).toBe(5);
    expect(openingProgress(89, 100).dissolve).toBe(0);
    expect(openingProgress(94.5, 100).dissolve).toBeCloseTo(0.5);
    expect(openingProgress(110, 100)).toEqual({
      phase: 1,
      plate: 5,
      dissolve: 1,
    });
  });
  it("uses project evidence plates instead of loading the archived hand scene", () => {
    const html = renderToStaticMarkup(<EntryExperience onEnter={() => {}} />);
    expect(html.match(/class="depth-plate frame-/g)).toHaveLength(6);
    expect(html).toContain("/brand/mark-3d.png");
    expect(html).toContain("136075");
    expect(html).toContain("8312");
    expect(html).toContain("6815");
    expect(html).toContain("Not parsed");
    expect(html).not.toContain("/field-report/");
    expect(html).not.toContain("/gallery/fields.png");
    expect(html).toContain("not accuracy claims");
    expect(html.match(/<button/g)).toHaveLength(1);
    expect(html).toContain("Scroll forward through the introduction");
    expect(html).not.toContain("Skip to the site");
    expect(html).not.toContain("iframe");
    expect(html).not.toContain("light-study");
  });
  it("ships six small portrait plates with provenance to saved records", () => {
    const provenance = JSON.parse(
      readFileSync(asset("gallery/provenance.json"), "utf8"),
    );
    const latest = JSON.parse(
      readFileSync(asset("results/latest.json"), "utf8"),
    );
    const manifest = JSON.parse(
      readFileSync(asset(latest.manifest.replace(/^\//, "")), "utf8"),
    );
    expect(provenance.capture_run).toBe(manifest.run_id);
    const supplemental = JSON.parse(
      readFileSync(asset("gallery/samples.json"), "utf8"),
    );
    expect(provenance.panels).toHaveLength(6);
    for (const panel of provenance.panels) {
      const png = readFileSync(asset(`gallery/${panel.file}`));
      expect(png.subarray(1, 4).toString()).toBe("PNG");
      expect(png.readUInt32BE(16)).toBe(1200);
      expect(png.readUInt32BE(20)).toBe(1500);
      expect(png.length).toBeLessThan(1_000_000);
      for (const id of panel.sources)
        expect(
          panel.capture === "supplemental"
            ? supplemental.studies.some(
                (study: { source_id: string; split: string }) =>
                  study.source_id === id && study.split === "dev",
              )
            : manifest.records.some(
                (record: { id: string }) => record.id === id,
              ),
        ).toBe(true);
    }
  });
});
