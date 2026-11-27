import { useRef, useState } from "react";
import { LeafThrough, type LeafThroughHandle } from "leafthrough/react";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { reportNotes as notes } from "../../generated/report";
const pages = notes.map((note, i) => ({
  src: `/field-report/${i + 1}.png`,
  alt: `ChequeVerify field notes: ${note.title}`,
  text: note.text,
}));
export default function ResearchBook() {
  const ref = useRef<LeafThroughHandle>(null);
  const [page, setPage] = useState(0),
    [last, setLast] = useState(0),
    [plain, setPlain] = useState(false),
    [error, setError] = useState(false);
  return (
    <>
      <div className="book-topline">
        <span>CHEQUEVERIFY / SIX PAGES OF EVIDENCE</span>
        <button onClick={() => setPlain(!plain)}>
          {plain ? "Return to 3D" : "Read without 3D"}
        </button>
      </div>
      <LeafThrough
        ref={ref}
        pages={pages}
        className="research-book"
        layout="auto"
        pageAspect={1600 / 1200}
        maxPixelRatio={2}
        preload={2}
        bleed={true}
        loop={false}
        plain={plain}
        label="ChequeVerify project field notes"
        paper={{
          grain: true,
          grainStrength: 0.025,
          showThrough: 0,
          inkGloss: 0.06,
        }}
        lighting={{ shadows: true, shadowMapSize: 1024, floorShadow: 0.12 }}
        motion={{ speed: 0.85, reducedMotion: "auto" }}
        onPageChange={(d) => {
          setPage(d.page);
          setLast(Math.max(...d.visiblePages));
        }}
        onError={() => setError(true)}
      />
      <div className="book-controls">
        <button
          aria-label="Previous field notes pages"
          disabled={page === 0}
          onClick={() => ref.current?.prev()}
        >
          <ArrowLeft size={20} aria-hidden="true" />
        </button>
        <span aria-live="polite">
          {page + 1}
          {last > page ? `–${last + 1}` : ""} / {notes.length}
        </span>
        <button
          aria-label="Next field notes pages"
          disabled={last >= notes.length - 1}
          onClick={() => ref.current?.next()}
        >
          <ArrowRight size={20} aria-hidden="true" />
        </button>
        <a href={pages[page].src} target="_blank" rel="noreferrer">
          View page PNG ↗
        </a>
      </div>
      {error && (
        <p role="status">
          The 3D reader could not load a page. The complete text is available
          below.
        </p>
      )}
      <details
        className="reading-notes"
        id="reading-notes"
        open={plain || undefined}
      >
        <summary>Text version</summary>
        {notes.map((note) => (
          <article key={note.title}>
            <h3>{note.title}</h3>
            <p>{note.text}</p>
          </article>
        ))}
      </details>
    </>
  );
}
