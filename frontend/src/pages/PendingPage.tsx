import { Link } from "react-router-dom";
import { ScanLine, CircleDashed } from "lucide-react";
export function PendingPage({
  title,
  milestone,
  description,
}: {
  title: string;
  milestone: string;
  description: string;
}) {
  return (
    <div className="pending-workspace">
      <p className="eyebrow">CHEQUEVERIFY / WORKSPACE</p>
      <h1>{title}</h1>
      <p className="pending-lead">{description}</p>
      <section className="pending-panel">
        <div className="pending-illustration" aria-hidden="true">
          <div className="document-outline">
            <ScanLine size={52} strokeWidth={1} />
            <span />
            <span />
            <span />
          </div>
        </div>
        <div className="pending-content">
          <span className="pending-tag">
            <CircleDashed size={16} aria-hidden="true" />
            Pending {milestone}
          </span>
          <h2>This workspace is being prepared.</h2>
          <p>
            The foundation is ready. The input controls and recognition flow for
            this workspace are part of the next implementation stage.
          </p>
          <Link className="button primary" to="/dashboard">
            Back to overview
          </Link>
        </div>
      </section>
    </div>
  );
}
