import { lazy, Suspense, useEffect, useId, useRef, useState } from "react";
import { ArrowUpRight, Send, X } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useSessionRuns } from "../../lib/sessionRuns";

const Character3D = lazy(() => import("./GuideCharacter3D"));
export function GuideCharacter() {
  return (
    <span className="guide-character" aria-hidden="true">
      <Suspense fallback={<span className="guide-model-fallback">✦</span>}>
        <Character3D />
      </Suspense>
    </span>
  );
}
export function guideAnswer(question: string) {
  const q = question.toLowerCase();
  if (/authentic|fraud|safe/.test(q))
    return "ChequeVerify compares recognised amounts. Agreement does not establish cheque authenticity or detect fraud. The final judgement belongs to a person.";
  if (/athn|scale|baseline|prepar/.test(q))
    return "Baseline uses the original preparation. ATHN estimates text height and adjusts its scale before the same frozen LoGo-HTR recogniser. Compare both on the same field in the Live lab.";
  if (/bench|cer|chart|heatmap|research/.test(q))
    return "CER counts substitutions, deletions and insertions per reference character; lower is better, and insertions can push it above 100%. The heatmap shows actual pair-decision counts. Research is frozen; filters change the view, not the results.";
  if (/null|parse|review|wrong|fail/.test(q))
    return "A null value means the raw reading did not satisfy the strict amount grammar. It stays unresolved. If either field cannot be parsed, verification asks for human review. Raw text is never silently corrected.";
  if (/key|groq|api|chat/.test(q))
    return "I am the local field guide. Groq chat will be connected later through a server-side endpoint; no API key is stored in this browser.";
  if (/latency|time|slow/.test(q))
    return "The live timer measures how long this browser waits. Result cards show the backend's own preprocessing, queue and inference timings. Calls run sequentially; large written fields can take longer.";
  return "Open the Live lab, choose a DEV sample or upload a synthetic/consented field crop, then run recognition. Choose Compare both for baseline and ATHN on identical pixels. To compare two amounts, open Cheque verification and provide a figures crop and a words crop.";
}
export function WorkspaceAssistant() {
  const panelId = useId();
  const [open, setOpen] = useState(false),
    [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "guide"; text: string }[]
  >([]);
  const location = useLocation(),
    runs = useSessionRuns();
  const trigger = useRef<HTMLButtonElement>(null),
    input = useRef<HTMLInputElement>(null),
    log = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (open) input.current?.focus();
  }, [open]);
  useEffect(() => {
    log.current?.scrollTo({ top: log.current.scrollHeight });
  }, [messages]);
  function ask(value: string) {
    if (!value.trim()) return;
    setMessages((m) => [
      ...m,
      { role: "user", text: value.slice(0, 500) },
      { role: "guide", text: guideAnswer(value) },
    ]);
    setQuestion("");
  }
  function close() {
    setOpen(false);
    trigger.current?.focus();
  }
  return (
    <>
      <button
        ref={trigger}
        className="guide-trigger"
        onClick={() => setOpen(!open)}
        aria-label={open ? "Close field guide" : "Open field guide"}
        aria-expanded={open}
        aria-controls={panelId}
      >
        <GuideCharacter />
        <span>
          <strong>Pip, your field guide</strong>
          <small>A little help, closer to the evidence.</small>
        </span>
        <span className="guide-status" />
      </button>
      {open && (
        <section
          id={panelId}
          className="guide-panel"
          role="dialog"
          aria-label="Pip field guide"
          onKeyDown={(e) => {
            if (e.key === "Escape") close();
          }}
        >
          <header>
            <div>
              <strong>Pip / Field guide</strong>
              <small>Local help · Groq connection later</small>
            </div>
            <button onClick={close} aria-label="Close field guide panel">
              <X size={18} />
            </button>
          </header>
          <div
            className="guide-messages"
            ref={log}
            role="log"
            aria-live="polite"
          >
            <p className="guide-bubble">
              {location.pathname === "/benchmarks"
                ? "Need a hand reading these results? I can explain CER, the heatmap, and the limits of the study."
                : "Let's follow the evidence. I can help you run a field, compare methods, or understand an unresolved amount."}{" "}
              {runs.length
                ? `${runs.length} live requests recorded in this tab.`
                : "Your live session is ready to start."}
            </p>
            {messages.map((m, i) => (
              <p key={i} className={`guide-bubble ${m.role}`}>
                {m.text}
              </p>
            ))}
          </div>
          <div className="guide-suggestions">
            {[
              "How do I test a field?",
              "What does ATHN do?",
              "Why human review?",
            ].map((q) => (
              <button key={q} onClick={() => ask(q)}>
                {q}
              </button>
            ))}
          </div>
          <Link to="/recognize" onClick={() => setOpen(false)}>
            Open the live lab <ArrowUpRight size={14} />
          </Link>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(question);
            }}
          >
            <input
              ref={input}
              aria-label="Ask the local field guide"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              maxLength={500}
              placeholder="Ask about the workspace…"
            />
            <button disabled={!question.trim()} aria-label="Ask Pip">
              <Send size={17} />
            </button>
          </form>
        </section>
      )}
    </>
  );
}
