import { describe, expect, it } from "vitest";
import { Mesh, MeshBasicMaterial, Raycaster, Vector3 } from "three";
import { createBrandGeometry } from "../src/components/visuals/OpeningBrandScene";
import { OPENING, nextOpeningStop, openingPose, openingProgress,
  specimenVisibility } from "../src/components/visuals/openingMotion";

describe("Scroll-led identity to evidence", () => {
  it("holds the assembled dots before forming a solid and docking", () => {
    const dots = openingPose(0.2);
    expect(dots.assembly).toBe(1);
    expect(dots.solid).toBe(0);
    expect(dots.dock).toBe(0);
    expect(dots.gallery).toBe(0);
    const solid = openingPose(0.29);
    expect(solid.solid).toBe(1);
    expect(solid.dock).toBe(0);
    expect(solid.ribbons).toBe(0);
    expect(openingPose(OPENING.galleryStart)).toMatchObject({ dock: 1, gallery: 1 });
  });
  it("advances all identity holds, all six specimens, and the final handover", () => {
    let phase = 0;
    const frames: number[] = [];
    for (let i = 0; i < 12 && phase < 1; i++) {
      const next = nextOpeningStop(phase);
      expect(next).toBeGreaterThan(phase);
      phase = next;
      if (phase >= OPENING.galleryStart && phase <= OPENING.galleryEnd)
        frames.push(Math.round(openingProgress(phase, 1).plate));
    }
    expect(frames).toEqual([0, 1, 2, 3, 4, 5]);
    expect(phase).toBe(1);
    expect(nextOpeningStop(1)).toBe(1);
  });
  it("uses static compositions and an immediate dock for reduced motion", () => {
    expect(openingPose(.1, true)).toEqual({ assembly: 1, solid: 1, dock: 0, gallery: 0, ribbons: 1 });
    expect(openingPose(.34, true)).toEqual({ assembly: 1, solid: 1, dock: 0, gallery: 0, ribbons: 0 });
    expect(openingPose(.39, true)).toEqual({ assembly: 1, solid: 1, dock: 1, gallery: 1, ribbons: 0 });
  });
  it("keeps specimen text isolated across the entire extended timeline", () => {
    for (let step = 0; step <= 1000; step++) {
      const { phase, plate } = openingProgress(step, 1000);
      const pose = openingPose(phase);
      for (const reduced of [false, true]) {
        const painted = Array.from({ length: 6 }, (_, i) =>
          specimenVisibility(i, plate, reduced) * pose.gallery).filter(n => n > .001);
        expect(painted.length).toBeLessThanOrEqual(1);
        if (phase <= .325) expect(painted).toHaveLength(0);
      }
    }
    expect(openingProgress(-50, 100).phase).toBe(0);
    expect(openingProgress(200, 100).dissolve).toBe(1);
  });
});

describe("Original brand geometry", () => {
  it("retains the bracket, open aperture and check with genuine extrusion", () => {
    const geometry = createBrandGeometry(), material = new MeshBasicMaterial();
    const mesh = new Mesh(geometry, material);
    geometry.computeBoundingBox();
    const box = geometry.boundingBox!;
    expect(box.max.z - box.min.z).toBeCloseTo(.218, 3);
    const intersects = (x: number, y: number) => new Raycaster(
      new Vector3((x - 35.5) / 49, (32.5 - y) / 49, 3),
      new Vector3(0, 0, -1)).intersectObject(mesh).length > 0;
    expect(intersects(12, 30)).toBe(true); // bracket
    expect(intersects(55, 22)).toBe(true); // check
    expect(intersects(23, 25)).toBe(false); // retained aperture
    expect(intersects(48, 48)).toBe(false); // outside the silhouette
    geometry.dispose(); material.dispose();
  });
});
