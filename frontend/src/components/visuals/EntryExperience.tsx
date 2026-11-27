import { lazy, Suspense, useEffect, useRef } from "react";
import { ArrowUpRight } from "lucide-react";
const HologramLogo = lazy(() => import("./HologramLogo"));

export function EntryExperience({ onEnter }: { onEnter: () => void }) {
  const button = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    button.current?.focus({ preventScroll: true });
  }, []);
  return (
    <section
      className="entry-experience branded-entry"
      aria-label="ChequeVerify light introduction"
    >
      <img className="entry-hand" src="/brand/hand-light.png" alt="" />
      <div className="entry-vignette" />
      <div className="entry-hologram" aria-hidden="true">
        <Suspense
          fallback={
            <img
              className="entry-logo-fallback"
              src="/brand/mark-3d.png"
              alt=""
            />
          }
        >
          <HologramLogo />
        </Suspense>
      </div>
      <button
        ref={button}
        className="entry-continue"
        onClick={onEnter}
        aria-label="Enter ChequeVerify"
        title="Enter ChequeVerify"
      >
        <ArrowUpRight size={27} strokeWidth={1.5} aria-hidden="true" />
      </button>
    </section>
  );
}
