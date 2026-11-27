import { useRef, useState } from "react";
import { LeafThrough, type LeafThroughHandle } from "leafthrough/react";

const notes = [
  {
    title: "A closer look",
    text: "ChequeVerify reads the amount in figures and the amount in words, then compares the recognised values. An academic prototype for human review.",
  },
  {
    title: "One cheque. Two expressions.",
    text: "The amount appears in figures and in English words. Users select both fields themselves. Automatic field detection is not implemented.",
  },
  {
    title: "The recogniser",
    text: "LoGo-HTR uses the authors’ released checkpoint on CPU. Its weights remain unchanged. The baseline uses the original transform and decoding pipeline.",
  },
  {
    title: "A question of scale",
    text: "ATHN is adaptive text-height normalisation: a training-free preprocessing step before the same recogniser. The configuration was selected on the development split and frozen before test evaluation.",
  },
  {
    title: "Agreement needs context",
    text: "Amounts agree when both recognised values parse and match. Amounts differ when both parse and disagree. Human review is needed when either cannot be parsed. Agreement is not proof of authenticity.",
  },
  {
    title: "Evidence before certainty",
    text: "Genuine handwriting and synthetic data are reported separately. Every synthetic pair went to review in the locked test. The genuine-handwriting change was not statistically significant. Saved research results must be read alongside these limitations.",
  },
];
const pages = notes.map((note, i) => ({
  src: `/field-notes/${i + 1}.svg`,
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
        <span>CHEQUEVERIFY — FIELD NOTES</span>
        <button onClick={() => setPlain(!plain)}>
          {plain ? "Return to 3D" : "Read without 3D"}
        </button>
      </div>
      <LeafThrough
        ref={ref}
        pages={pages}
        className="research-book"
        layout="auto"
        pageAspect={1240 / 900}
        maxPixelRatio={1.25}
        preload={2}
        bleed={true}
        loop={false}
        plain={plain}
        label="ChequeVerify project field notes"
        paper={{
          grain: true,
          grainStrength: 0.12,
          showThrough: 0.02,
          inkGloss: 0.2,
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
          Previous
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
          Next
        </button>
      </div>
      <p className="book-hint">
        Drag a page to turn it. Use the controls or arrow keys when the reader
        is focused.
      </p>
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
        <summary>Read the complete field notes as text</summary>
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
