import { Link } from "react-router-dom";
import { ScanLine } from "lucide-react";
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
    <>
      <p className="eyebrow">APPLICATION WORKSPACE</p>
      <h1>{title}</h1>
      <section className="pending-panel">
        <ScanLine size={38} strokeWidth={1} aria-hidden="true" />
        <span className="mode-tag">PENDING {milestone}</span>
        <h2>This workspace is next.</h2>
        <p>{description}</p>
        <p>
          This route is part of the foundation. Its controls and API integration
          are not implemented yet.
        </p>
        <Link className="button primary" to="/dashboard">
          Return to dashboard
        </Link>
      </section>
    </>
  );
}
