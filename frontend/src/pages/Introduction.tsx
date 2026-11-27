import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Brand } from "../components/ui/Brand";
import { EntryExperience } from "../components/visuals/EntryExperience";
const WaveGridScene = lazy(() => import("../components/visuals/WaveGridScene"));
const ResearchBook = lazy(() => import("../components/visuals/ResearchBook"));
export function Introduction() {
  const navigate = useNavigate();
  const [entered, setEntered] = useState(false);
  const [bookVisible, setBookVisible] = useState(false);
  const bookSection = useRef<HTMLElement>(null);
  const hero = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    document.title = "ChequeVerify — Look closer";
  }, []);
  useEffect(() => {
    if (!entered) return;
    window.scrollTo(0, 0);
    hero.current?.focus({ preventScroll: true });
    const observer = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setBookVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "250px" },
    );
    if (bookSection.current) observer.observe(bookSection.current);
    return () => observer.disconnect();
  }, [entered]);
  if (!entered)
    return (
      <EntryExperience
        onEnter={() => {
          navigate("/", { replace: true });
          setEntered(true);
          window.scrollTo(0, 0);
        }}
      />
    );
  return (
    <main className="vision-landing">
      <a className="skip-link" href="#field-notes">
        Skip to project field notes
      </a>
      <header className="vision-header">
        <Link to="/" aria-label="ChequeVerify introduction">
          <Brand />
        </Link>
        <nav aria-label="Landing navigation">
          <a href="#field-notes">Field notes</a>
          <Link to="/dashboard">
            Open workspace <span aria-hidden="true">↗</span>
          </Link>
        </nav>
      </header>
      <section className="wave-hero" aria-labelledby="hero-title">
        <div className="wave-visual" aria-hidden="true">
          <Suspense fallback={null}>
            <WaveGridScene />
          </Suspense>
        </div>
        <div className="hero-copy">
          <p className="vision-kicker">A STUDY IN MACHINE PERCEPTION</p>
          <h1 id="hero-title" ref={hero} tabIndex={-1}>
            Read the ink.
            <br />
            <span>See the difference.</span>
          </h1>
          <p className="vision-description">
            Two handwritten amounts. A recognition model.
            <br className="desktop-break" /> A comparison that stays open to
            human judgement.
          </p>
          <div className="vision-actions">
            <Link to="/dashboard" className="vision-primary">
              Explore the workspace <span aria-hidden="true">↗</span>
            </Link>
            <a href="#field-notes" className="vision-text-link">
              Understand the method
            </a>
          </div>
          <p className="vision-fineprint">
            Research prototype · LoGo-HTR + ATHN
          </p>
        </div>
        <p className="wave-instruction">
          MOVE ACROSS THE SURFACE / A STUDY IN PERCEPTION
        </p>
        <div className="hero-bottom">
          <span>RECOGNISE / PARSE / COMPARE</span>
          <a href="#field-notes">
            SCROLL TO DISCOVER <span aria-hidden="true">↓</span>
          </a>
          <span>01 — THE OBSERVATION</span>
        </div>
      </section>
      <section
        className="field-notes"
        id="field-notes"
        ref={bookSection}
        aria-labelledby="notes-title"
      >
        <div className="notes-intro">
          <p className="vision-kicker">02 — THE FIELD NOTES</p>
          <h2 id="notes-title">
            The method,
            <br />
            on paper.
          </h2>
          <p>
            Turn through the question, the recogniser, and the training-free
            change behind ChequeVerify.
          </p>
          <p className="notes-aside">
            A short project companion. The live model status is in the
            workspace; these pages explain the method.
          </p>
          <a
            className="notes-link"
            href="#reading-notes"
            onClick={() => {
              const details = document.getElementById("reading-notes");
              if (details instanceof HTMLDetailsElement) details.open = true;
            }}
          >
            Prefer plain text? Read the notes
          </a>
        </div>
        <div className="book-column">
          {bookVisible ? (
            <Suspense
              fallback={<p className="book-loading">Opening field notes…</p>}
            >
              <ResearchBook />
            </Suspense>
          ) : (
            <div className="book-loading">Field notes</div>
          )}
        </div>
      </section>
      <section className="landing-closing">
        <p className="vision-kicker">FROM THE STUDY TO THE SYSTEM</p>
        <h2>
          Put the model
          <br />
          in perspective.
        </h2>
        <Link to="/dashboard" className="vision-primary">
          Open the dashboard <span aria-hidden="true">↗</span>
        </Link>
        <p>
          An agreement between recognised amounts is not proof of cheque
          authenticity.
        </p>
      </section>
      <footer className="vision-footer">
        <Brand />
        <span>Computer Vision · Fall 2026</span>
        <button
          onClick={() => {
            navigate("/", { replace: true });
            setEntered(false);
            setBookVisible(false);
            window.scrollTo(0, 0);
          }}
        >
          Replay light introduction
        </button>
        <a href="/visual-credits.txt" target="_blank" rel="noreferrer">
          Visual credits
        </a>
      </footer>
    </main>
  );
}

import "../landing.css";
