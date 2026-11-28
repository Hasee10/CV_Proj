import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowUp, ArrowUpRight, Menu, RotateCcw } from "lucide-react";
import { Brand } from "../components/ui/Brand";
import { EntryExperience } from "../components/visuals/EntryExperience";
import { WorkflowSection } from "../components/visuals/LandingStudy";
import { VisionSpecimen } from "../components/visuals/VisionSpecimen";
import { ResearchEvidence } from "../components/visuals/ResearchEvidence";
import { useSavedCapture } from "../hooks/useSavedCapture";
const WaveGridScene = lazy(() => import("../components/visuals/WaveGridScene"));
const ResearchBook = lazy(() => import("../components/visuals/ResearchBook"));
export function Introduction() {
  const navigate = useNavigate();
  const capture = useSavedCapture();
  const [entered, setEntered] = useState(
    () => typeof window !== "undefined" && Boolean(window.location.hash),
  );
  const [bookVisible, setBookVisible] = useState(false);
  const bookSection = useRef<HTMLElement>(null);
  const hero = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    document.title = "ChequeVerify — Look closer";
  }, []);
  useEffect(() => {
    if (entered) {
      if (window.location.hash) {
        requestAnimationFrame(() =>
          document
            .getElementById(window.location.hash.slice(1))
            ?.scrollIntoView(),
        );
      } else {
        window.scrollTo(0, 0);
        hero.current?.focus({ preventScroll: true });
      }
    }
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
  return (
    <>
      {!entered && (
        <EntryExperience
          onEnter={() => {
            navigate("/", { replace: true });
            setEntered(true);
            window.scrollTo(0, 0);
          }}
        />
      )}
      <main
        className={`vision-landing${entered ? "" : " opening-underlay"}`}
        id="top"
        inert={!entered || undefined}
        aria-hidden={!entered || undefined}
      >
        <a className="skip-link" href="#field-notes">
          Skip to project field notes
        </a>
        <div className="header-dock">
          <header className="vision-header">
            <Link
              to="/"
              className="header-identity"
              aria-label="ChequeVerify introduction"
            >
              <Brand />
            </Link>
            <nav className="header-sections" aria-label="Landing navigation">
              <a href="#workflow">
                <span aria-hidden="true">01</span> How it works
              </a>
              <a href="#field-notes">
                <span aria-hidden="true">02</span> Field report
              </a>
              <a href="#evidence">
                <span aria-hidden="true">03</span> Evidence
              </a>
            </nav>
            <details className="header-mobile-nav">
              <summary aria-label="Browse sections">
                <Menu size={19} aria-hidden="true" />
              </summary>
              <nav
                aria-label="Mobile landing navigation"
                onClick={(event) => {
                  if ((event.target as HTMLElement).closest("a"))
                    event.currentTarget.closest("details")!.open = false;
                }}
              >
                <a href="#workflow">
                  How it works <span aria-hidden="true">↘</span>
                </a>
                <a href="#field-notes">
                  Field report <span aria-hidden="true">↘</span>
                </a>
                <a href="#evidence">
                  Evidence <span aria-hidden="true">↘</span>
                </a>
              </nav>
            </details>
            <Link
              to="/dashboard"
              className="header-workspace"
              aria-label="Enter workspace"
            >
              <span>
                <span className="header-cta-prefix">Enter </span>workspace
              </span>
              <span className="header-cta-arrow">
                <ArrowUpRight size={17} aria-hidden="true" />
              </span>
            </Link>
          </header>
        </div>
        <section
          className="wave-hero purposeful-hero"
          aria-labelledby="hero-title"
        >
          <div className="wave-visual" aria-hidden="true">
            <Suspense fallback={null}>
              <WaveGridScene />
            </Suspense>
          </div>
          <div className="hero-copy">
            <p className="vision-kicker">CHEQUE AMOUNT RECOGNITION</p>
            <h1 id="hero-title" ref={hero} tabIndex={-1}>
              Read the amount.
              <br />
              <span>Keep the evidence.</span>
            </h1>
            <p className="vision-description">
              Two handwritten amounts. One visible comparison. Read the figures
              and words, inspect the evidence, then make the final call.
            </p>
            <div className="vision-actions">
              <Link to="/verify" className="vision-primary">
                Compare two fields <span aria-hidden="true">↗</span>
              </Link>
              <a href="#workflow" className="vision-text-link">
                See how it works
              </a>
            </div>
          </div>
          <VisionSpecimen capture={capture} />
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
              Nine pages. Original inputs, real model outputs, and the research
              behind the comparison.
            </p>
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
        <ResearchEvidence capture={capture} />
        <section className="landing-closing">
          <div className="closing-copy">
            <p className="vision-kicker">EXPLORE THE WORKSPACE</p>
            <h2>
              The image.
              <br />
              The reading.
              <br />
              <span>The reason behind it.</span>
            </h2>
            <p>
              Follow a recorded example from its original pixels to the final
              comparison. Inspect each field, compare both methods, or make a
              fresh request.
            </p>
            <Link to="/verify" className="vision-primary">
              Inspect a real result <span aria-hidden="true">↗</span>
            </Link>
          </div>
          <div className="closing-path">
            <Link to="/verify">
              <span>01 / INSPECT</span>
              <h3>Keep the source in sight.</h3>
              <p>
                Original image, selected fields, and the comparison decision.
              </p>
              <b aria-hidden="true">↗</b>
            </Link>
            <Link to="/recognize">
              <span>02 / COMPARE</span>
              <h3>Understand the reading.</h3>
              <p>Baseline and ATHN results from the same input.</p>
              <b aria-hidden="true">↗</b>
            </Link>
            <Link to="/benchmarks">
              <span>03 / QUESTION</span>
              <h3>Read beyond the numbers.</h3>
              <p>Frozen research results, with their limits alongside them.</p>
              <b aria-hidden="true">↗</b>
            </Link>
            <p>
              Agreement checks values. It does not establish cheque
              authenticity.
            </p>
          </div>
        </section>
        <footer className="vision-footer">
          <div className="footer-masthead">
            <a
              href="#top"
              className="footer-wordmark"
              aria-label="ChequeVerify — back to top"
            >
              <Brand />
            </a>
            <div className="footer-purpose">
              <div className="footer-field-pair" aria-hidden="true">
                <span>Figures</span>
                <i />
                <span>Words</span>
              </div>
              <p>
                Two amounts.
                <br />
                One inspectable comparison.
              </p>
              <span>Computer vision, with the evidence in view.</span>
            </div>
          </div>
          <div className="footer-link-grid">
            <nav
              className="footer-navigation"
              aria-label="Footer workspace navigation"
            >
              <h2>
                <span aria-hidden="true">01</span> The workspace
              </h2>
              <Link to="/verify">
                Cheque verification{" "}
                <ArrowUpRight size={15} aria-hidden="true" />
              </Link>
              <Link to="/recognize">
                Amount recognition <ArrowUpRight size={15} aria-hidden="true" />
              </Link>
              <Link to="/benchmarks">
                Research benchmarks{" "}
                <ArrowUpRight size={15} aria-hidden="true" />
              </Link>
            </nav>
            <nav
              className="footer-navigation"
              aria-label="Footer study navigation"
            >
              <h2>
                <span aria-hidden="true">02</span> The study
              </h2>
              <a href="#workflow">
                How it works <ArrowUp size={14} aria-hidden="true" />
              </a>
              <a href="#field-notes">
                Read the field report <ArrowUp size={14} aria-hidden="true" />
              </a>
              <a href="#evidence">
                Results in context <ArrowUp size={14} aria-hidden="true" />
              </a>
            </nav>
            <nav
              className="footer-navigation"
              aria-label="Footer experience navigation"
            >
              <h2>
                <span aria-hidden="true">03</span> The experience
              </h2>
              <button
                onClick={() => {
                  navigate("/", { replace: true });
                  setEntered(false);
                  setBookVisible(false);
                  window.scrollTo(0, 0);
                }}
              >
                Replay the introduction{" "}
                <RotateCcw size={14} aria-hidden="true" />
              </button>
              <a href="/visual-credits.txt" target="_blank" rel="noreferrer">
                Design & visual credits{" "}
                <ArrowUpRight size={15} aria-hidden="true" />
              </a>
              <a href="#top">
                Back to the top <ArrowUp size={14} aria-hidden="true" />
              </a>
            </nav>
          </div>
          <div className="footer-bottom">
            <span className="footer-research-label">
              <i aria-hidden="true" /> Research prototype · LoGo-HTR + ATHN
            </span>
            <span>Computer Vision / Fall 2026</span>
            <span>Evidence first. Human judgement always.</span>
          </div>
        </footer>
      </main>
    </>
  );
}

import "../landing.css";
