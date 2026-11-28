import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { LeafThrough, type LeafThroughHandle } from "leafthrough/react";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { reportNotes as notes } from "../../generated/report";
const pages = notes.map((note, i) => ({
  src: `/field-report/${i + 1}.png`,
  alt: `ChequeVerify field notes: ${note.title}`,
  text: note.text,
}));
const spreadQuery = "(min-width: 768px)";
function subscribeLayout(notify: () => void) {
  const query = matchMedia(spreadQuery);
  query.addEventListener("change", notify);
  return () => query.removeEventListener("change", notify);
}
export default function ResearchBook() {
  const desktop = useSyncExternalStore(
    subscribeLayout,
    () => matchMedia(spreadQuery).matches,
    () => false,
  );
  const ref = useRef<LeafThroughHandle>(null);
  const [page, setPage] = useState(0),
    [last, setLast] = useState(0),
    [error, setError] = useState(false);
  useEffect(() => {
    // The library does not emit a page-change event when a new layout mounts.
    // Align both the visible spread and its counter when crossing a breakpoint.
    const first = desktop && page > 0 ? Math.ceil(page / 2) * 2 - 1 : page;
    setPage(first);
    setLast(
      desktop && first > 0 ? Math.min(first + 1, notes.length - 1) : first,
    );
  }, [desktop, page]);
  return (
    <>
      <div className={`book-stage ${desktop ? "spread" : "single"}`}>
        <LeafThrough
          key={desktop ? "spread" : "single"}
          ref={ref}
          startPage={page}
          pages={pages}
          className="research-book"
          layout={desktop ? "spread" : "single"}
          pageAspect={1600 / 1200}
          maxPixelRatio={2}
          preload={2}
          bleed={true}
          loop={false}
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
      </div>
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
      </div>
      {error && (
        <p role="status">
          The reader could not load a page. The report text is available below.
        </p>
      )}
      <section
        className={error ? "reading-notes" : "sr-only"}
        aria-label="Field report text"
      >
        {notes.map((note) => (
          <article key={note.title}>
            <h3>{note.title}</h3>
            <p>{note.text}</p>
          </article>
        ))}
      </section>
    </>
  );
}
