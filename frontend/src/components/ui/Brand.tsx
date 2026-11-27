import { ScanLine } from "lucide-react";
export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <ScanLine size={23} strokeWidth={1.6} aria-hidden="true" />
      </span>
      ChequeVerify<span className="brand-period">.</span>
    </span>
  );
}
