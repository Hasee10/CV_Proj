import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Brand } from "../components/ui/Brand";
import { EntryExperience } from "../components/visuals/EntryExperience";
import {
  WorkflowSection,
  EvidenceSection,
} from "../components/visuals/LandingStudy";
import { useSavedCapture } from "../hooks/useSavedCapture";
const WaveGridScene = lazy(() => import("../components/visuals/WaveGridScene"));
const ResearchBook = lazy(() => import("../components/visuals/ResearchBook"));
export function Introduction() {
  const navigate = useNavigate();
  const capture = useSavedCapture();
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
          <a href="#workflow">How it works</a>
          <a href="#field-notes">Field report</a>
          <a href="#evidence">Evidence</a>
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
          <p className="vision-kicker">HANDWRITING, MADE READABLE</p>
          <h1 id="hero-title" ref={hero} tabIndex={-1}>
            Read the amount.
            <br />
            <span>See the whole picture.</span>
          </h1>
          <p className="vision-description">
            Recognise the amount in figures and in words. Compare their values,
            inspect the evidence, and keep the final judgement in human hands.
          </p>
          <div className="vision-actions">
            <Link to="/dashboard" className="vision-primary">
              Open the workspace <span aria-hidden="true">↗</span>
            </Link>
            <a href="#workflow" className="vision-text-link">
              See how it works
            </a>
          </div>
          <p className="vision-fineprint">
            Research prototype · LoGo-HTR + ATHN
          </p>
        </div>
      </section>
      <WorkflowSection capture={capture} />
      <section
        className="field-notes"
        id="field-notes"
        ref={bookSection}
        aria-labelledby="notes-title"
      >
        <div className="notes-intro">
          <p className="vision-kicker">THE FIELD REPORT</p>
          <h2 id="notes-title">A closer look at what the model sees.</h2>
          <p>
            Six pages. Original inputs, real model outputs, and the research
            behind the comparison.
          </p>

          <a
            className="notes-link"
            href="#reading-notes"
            onClick={() => {
              const details = document.getElementById("reading-notes");
              if (details instanceof HTMLDetailsElement) details.open = true;
            }}
          >
            Read the accessible text
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
      <EvidenceSection capture={capture} />
      <section className="landing-closing">
        <p className="vision-kicker">EXPLORE THE WORKSPACE</p>
        <h2>The image. The reading. The reason behind it.</h2>
        <Link to="/verify" className="vision-primary">
          Inspect a real result <span aria-hidden="true">↗</span>
        </Link>
        <p>
          Compare recorded examples and rerun them through the model. Agreement
          checks values; it does not establish cheque authenticity.
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
