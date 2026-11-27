import type { CaptureRecord, PairMetrics } from "../api/results";

export function roiRect(box: readonly number[]) {
  if (
    box.length !== 4 ||
    !box.every(Number.isFinite) ||
    box[2] <= box[0] ||
    box[3] <= box[1]
  )
    throw new Error("Invalid pixel ROI.");
  return {
    x: box[0],
    y: box[1],
    width: box[2] - box[0],
    height: box[3] - box[1],
  };
}
export function sameCapturedInput(a?: CaptureRecord, b?: CaptureRecord) {
  return Boolean(
    a?.image_sha256 && b?.image_sha256 && a.image_sha256 === b.image_sha256,
  );
}
export function percent(value: number | null | undefined) {
  if (value === null) return "n/a";
  if (value === undefined) return "Not reported";
  return new Intl.NumberFormat("en-GB", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}
export function decisionCounts(metrics: PairMetrics) {
  return (["accept", "flag", "review"] as const).map((key) => ({
    key,
    count: metrics.decisions[key] ?? 0,
  }));
}
export function automaticDecisions(metrics: PairMetrics) {
  return (metrics.decisions.accept ?? 0) + (metrics.decisions.flag ?? 0);
}
