import { useState } from "react";
import type { CaptureRecord, VerifyResult } from "../../api/results";
import { roiRect } from "../../lib/presentation";

export function EvidencePanel({
  record,
  rois,
}: {
  record: CaptureRecord;
  rois?: VerifyResult["rois"];
}) {
  const [size, setSize] = useState<{ width: number; height: number } | null>(
    null,
  );
  return (
    <section className="evidence-panel polish-card">
      <div className="panel-heading">
        <h2>Input evidence</h2>
        <span className="capture-chip">
          {record.synthetic ? "Synthetic" : "Genuine handwriting"}
        </span>
      </div>
      <p className="evidence-description">{record.description}</p>
      <div
        className={`inspection-stage ${rois ? "sheet-stage" : "field-stage"}`}
      >
        <img
          src={record.image}
          alt={
            rois
              ? "Original constructed demonstration sheet"
              : "Original development field crop"
          }
          hidden={Boolean(size)}
          onLoad={(e) =>
            setSize({
              width: e.currentTarget.naturalWidth,
              height: e.currentTarget.naturalHeight,
            })
          }
        />
        {size && (
          <svg
            className="evidence-svg"
            viewBox={`0 0 ${size.width} ${size.height}`}
            role="img"
            aria-label={
              rois
                ? "Original sheet with server-returned numeric and written regions"
                : "Original development field crop"
            }
          >
            <image
              href={record.image}
              width={size.width}
              height={size.height}
            />
            {rois &&
              (["numeric", "written"] as const).map((field) => {
                const bounds = roiRect(rois[`${field}_px`]);
                return (
                  <g key={field} className={`svg-roi ${field}`}>
                    <title>
                      {field === "numeric" ? "Figures" : "Words"}:{" "}
                      {bounds.width} × {bounds.height} pixels
                    </title>
                    <rect {...bounds} vectorEffect="non-scaling-stroke" />
                  </g>
                );
              })}
          </svg>
        )}
      </div>
      {size && (
        <>
          <div className="evidence-meta">
            <span>
              {size.width} × {size.height} px
            </span>
            <span>Original input · unchanged bytes</span>
          </div>
          {rois && (
            <div className="crop-previews">
              {(["numeric", "written"] as const).map((field) => {
                const bounds = roiRect(rois[`${field}_px`]);
                return (
                  <figure key={field} className={`crop-preview ${field}`}>
                    <figcaption>
                      <strong>
                        {field === "numeric" ? "01 · Figures" : "02 · Words"}
                      </strong>
                      <span>
                        {bounds.width} × {bounds.height} px
                      </span>
                    </figcaption>
                    <svg
                      viewBox={`${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}`}
                      role="img"
                      aria-label={`Magnified ${field} ROI from the original image`}
                    >
                      <image
                        href={record.image}
                        width={size.width}
                        height={size.height}
                      />
                    </svg>
                  </figure>
                );
              })}
            </div>
          )}
        </>
      )}
    </section>
  );
}
