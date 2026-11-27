import { lazy, Suspense, useEffect } from "react";
import { Link } from "react-router-dom";
import { Brand } from "../components/ui/Brand";
const LightScene = lazy(() => import("../components/visuals/LightScene"));
export function Introduction() {
  useEffect(() => {
    document.title = "ChequeVerify — Handwriting into evidence";
  }, []);
  return (
    <main className="introduction">
      <a className="skip-link" href="#intro-copy">
        Skip visual introduction
      </a>
      <Suspense fallback={null}>
        <LightScene />
      </Suspense>
      <header className="intro-header">
        <Link to="/" aria-label="ChequeVerify introduction">
          <Brand />
        </Link>
        <span>COMPUTER VISION / FALL 2026</span>
        <Link className="intro-nav" to="/dashboard">
          Open dashboard
        </Link>
      </header>
      <section className="intro-copy" id="intro-copy">
        <p className="eyebrow">HANDWRITING INTO EVIDENCE</p>
        <h1>
          Two amounts.
          <br />
          One closer look.
        </h1>
        <p className="intro-description">
          A computer vision workspace for reading handwritten cheque amounts and
          comparing what they say.
        </p>
        <Link className="button light" to="/dashboard">
          Enter the workspace
        </Link>
        <p className="intro-disclaimer">
          An academic prototype. Every result needs human interpretation.
        </p>
      </section>
      <div className="scene-caption">
        <span className="caption-line" />
        DOCUMENT STUDY
        <span>Procedural illustration · No recognition running</span>
      </div>
      <footer className="intro-footer">
        <span>RECOGNISE / PARSE / COMPARE</span>
        <span>LoGo-HTR + ATHN</span>
        <Link to="/dashboard">System overview</Link>
      </footer>
    </main>
  );
}
