export const clamp01 = (n: number) => Math.max(0, Math.min(1, n));
export const ease = (n: number) => {
  const t = clamp01(n);
  return t * t * (3 - 2 * t);
};

// Native scroll is the only timeline. These holds leave each transformation
// legible, and make arbitrary scroll jumps and reverse scrolling deterministic.
export const OPENING = {
  assemblyStart: 0.025,
  assemblyEnd: 0.15,
  solidStart: 0.225,
  solidEnd: 0.285,
  dockStart: 0.29,
  dockEnd: 0.375,
  galleryStart: 0.39,
  galleryEnd: 0.84,
  dissolveStart: 0.89,
} as const;

export function openingProgress(scroll: number, range: number) {
  const phase = clamp01(scroll / Math.max(1, range));
  return {
    phase,
    plate: clamp01((phase - OPENING.galleryStart) /
      (OPENING.galleryEnd - OPENING.galleryStart)) * 5,
    dissolve: ease((phase - OPENING.dissolveStart) / (1 - OPENING.dissolveStart)),
  };
}

export function openingPose(phase: number, reduced = false) {
  if (reduced) return {
    assembly: 1, solid: 1, dock: Number(phase >= OPENING.dockEnd),
    gallery: Number(phase >= OPENING.dockEnd), ribbons: Number(phase < 0.15),
  };
  return {
    assembly: ease((phase - OPENING.assemblyStart) /
      (OPENING.assemblyEnd - OPENING.assemblyStart)),
    solid: ease((phase - OPENING.solidStart) / (OPENING.solidEnd - OPENING.solidStart)),
    dock: ease((phase - OPENING.dockStart) / (OPENING.dockEnd - OPENING.dockStart)),
    gallery: ease((phase - 0.325) / 0.05),
    ribbons: 1 - ease((phase - 0.04) / 0.17),
  };
}

export function nextOpeningStop(phase: number) {
  const stops = [0.15, 0.225, 0.29, OPENING.galleryStart,
    ...Array.from({ length: 5 }, (_, i) => OPENING.galleryStart +
      (i + 1) / 5 * (OPENING.galleryEnd - OPENING.galleryStart)), 1];
  return stops.find((stop) => stop > phase + 0.008) ?? 1;
}

export function specimenVisibility(index: number, plate: number, reduced = false) {
  if (reduced) return index === Math.round(plate) ? 1 : 0;
  const delta = index - plate;
  if (delta < -1 || delta > 1) return 0;
  return delta <= 0 ? 1 - ease((-delta - 0.18) / 0.32)
    : ease((1 - delta - 0.5) / 0.32);
}

export type LogoAnchor = { x: number; y: number; height: number };
export type OpeningSceneState = {
  phase: number;
  logoOpacity: number;
  anchor: LogoAnchor;
  siteAnchor: LogoAnchor;
  reduced: boolean;
};
