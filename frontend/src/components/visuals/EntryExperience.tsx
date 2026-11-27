import { useEffect, useRef, useState } from "react";
import { Brand } from "../ui/Brand";
export function EntryExperience({ onEnter }: { onEnter: () => void }) {
  const [loaded, setLoaded] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const [reduced, setReduced] = useState(
    () => matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    const query = matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    button.current?.focus({ preventScroll: true });
  }, []);
  return (
    <section
      className="entry-experience"
      aria-label="Volumetric light introduction"
    >
      {!reduced && (
        <iframe
          className="entry-scene"
          src="https://cullenwebber.github.io/three-volumetric-light/"
          title="Volumetric light and animated hand by Cullen Webber"
          sandbox="allow-scripts allow-same-origin"
          referrerPolicy="no-referrer"
          onLoad={() => setLoaded(true)}
        />
      )}
      <div className="entry-shade" />
      <header className="entry-header">
        <Brand />
        <button ref={button} onClick={onEnter}>
          Skip introduction
        </button>
      </header>
      <div className="entry-bottom">
        <div>
          <p className="entry-kicker">CHEQUEVERIFY / COMPUTER VISION</p>
          <h1>
            A closer look
            <br />
            changes everything.
          </h1>
          <p>Handwriting. Recognition. Human judgement.</p>
        </div>
        <button className="enter-button" onClick={onEnter}>
          Enter ChequeVerify <span aria-hidden="true">↗</span>
        </button>
      </div>
      <footer className="entry-credit">
        <span>
          {reduced
            ? "Still introduction · reduced motion"
            : loaded
              ? "Interactive light study"
              : "Loading external light study — you can enter immediately"}
        </span>
        <a
          href="https://cullenwebber.github.io/three-volumetric-light/"
          target="_blank"
          rel="noreferrer"
        >
          Light study by Cullen Webber
        </a>
      </footer>
    </section>
  );
}
