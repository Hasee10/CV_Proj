import { useEffect, useRef } from "react";
import { ArrowUpRight } from "lucide-react";

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
      <iframe
        className="entry-scene"
        src="/light-study/index.html"
        title="Animated hand and volumetric light with the ChequeVerify logo"
      />
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
