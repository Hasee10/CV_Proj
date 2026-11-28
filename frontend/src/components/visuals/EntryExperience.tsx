import { useEffect, useRef } from "react";
import { ArrowDown, ArrowUpRight, ScanLine } from "lucide-react";
import { labSamples } from "../../lib/sampleLibrary";

export const openingFrames = [
  {
    sample: 0,
    title: "Begin with the pixels.",
    label: "01 / THE INPUT",
    accent: "#816790",
    color: [243, 239, 246],
    side: 1,
  },
  {
    sample: 1,
    title: "Scale changes the reading.",
    label: "02 / PREPARATION",
    accent: "#957548",
    color: [247, 241, 229],
    side: -1,
  },
  {
    sample: 2,
    title: "Read what the model read.",
    label: "03 / RECOGNITION",
    accent: "#527c75",
    color: [235, 243, 239],
    side: 1,
  },
  {
    sample: 4,
    title: "Keep the error in view.",
    label: "04 / THE EVIDENCE",
    accent: "#a76e5b",
    color: [248, 240, 235],
    side: -1,
  },
  {
    sample: 5,
    title: "Small marks. Real consequences.",
    label: "05 / THE DETAIL",
    accent: "#736fa1",
    color: [241, 239, 248],
    side: -1,
  },
  {
    sample: 3,
    title: "Leave room for judgement.",
    label: "06 / HUMAN REVIEW",
    accent: "#947940",
    color: [247, 244, 236],
    side: 1,
  },
];
const chapters = openingFrames;

export function openingProgress(scroll: number, range: number) {
  const phase = Math.max(0, Math.min(1, scroll / Math.max(1, range)));
  const fade = Math.max(0, Math.min(1, (phase - 0.76) / 0.24));
  return {
    phase,
    plate: Math.min(
      chapters.length - 1,
      (phase / 0.72) * (chapters.length - 1),
    ),
    dissolve: fade * fade * (3 - 2 * fade),
  };
}

const smooth = (value: number) => {
  const t = Math.max(0, Math.min(1, value));
  return t * t * (3 - 2 * t);
};
// Outgoing and incoming content have separate visibility windows. At most one
// panel can be visible, including while scrolling backwards or jumping quickly.
export function specimenVisibility(
  index: number,
  plate: number,
  reduced = false,
) {
  if (reduced) return index === Math.round(plate) ? 1 : 0;
  const delta = index - plate;
  if (delta < -1 || delta > 1) return 0;
  return delta <= 0
    ? 1 - smooth((-delta - 0.18) / 0.32)
    : smooth((1 - delta - 0.5) / 0.32);
}

export function EntryExperience({ onEnter }: { onEnter: () => void }) {
  const root = useRef<HTMLElement>(null),
    stage = useRef<HTMLDivElement>(null);
  const plates = useRef<(HTMLElement | null)[]>([]),
    enter = useRef(onEnter);
  useEffect(() => {
    enter.current = onEnter;
  }, [onEnter]);
  useEffect(() => {
    const section = root.current!,
      reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const previousRestoration = history.scrollRestoration;
    history.scrollRestoration = "manual";
    scrollTo(0, 0);
    let frame = 0,
      completed = false;
    function update() {
      frame = 0;
      if (completed) return;
      const { phase, plate, dissolve } = openingProgress(
        -section.getBoundingClientRect().top,
        section.offsetHeight - innerHeight,
      );
      const first = Math.floor(plate),
        weight = plate - first;
      const a = chapters[first].color,
        b = chapters[Math.min(chapters.length - 1, first + 1)].color;
      stage.current!.style.backgroundColor = `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * weight)).join(",")})`;
      stage.current!.style.opacity = String(1 - dissolve);

      plates.current.forEach((image, index) => {
        if (!image) return;
        const delta = index - plate;
        const direction = chapters[index].side;
        const opacity = specimenVisibility(index, plate, reduced.matches);
        image.style.opacity = String(opacity);
        image.style.visibility = opacity > 0.001 ? "visible" : "hidden";
        image.style.transform = reduced.matches
          ? "translate(-50%, -50%)"
          : `translate3d(calc(-50% + ${delta * 14 * direction}vw), calc(-50% + ${delta * 2 - dissolve * 1.5}vh), ${-delta * 240 + dissolve * 70}px) rotateY(${-delta * 7 * direction}deg)`;
        image.dataset.visible = opacity > 0.001 ? "true" : "false";
        image.style.zIndex = String(10 - index);
      });
      if (phase >= 0.9995) {
        completed = true;
        stage.current!.style.opacity = "0";
        // The site is already held in the same viewport beneath the overlay.
        // Reset its scroll before releasing it, preserving the exact hero frame.
        scrollTo(0, 0);
        enter.current();
      }
    }
    function schedule() {
      if (!frame && !completed) frame = requestAnimationFrame(update);
    }
    addEventListener("scroll", schedule, { passive: true });
    addEventListener("resize", schedule);
    reduced.addEventListener("change", schedule);
    update();
    return () => {
      cancelAnimationFrame(frame);
      history.scrollRestoration = previousRestoration;
      removeEventListener("scroll", schedule);
      removeEventListener("resize", schedule);
      reduced.removeEventListener("change", schedule);
    };
  }, []);
  function forward() {
    const section = root.current!;
    const range = section.offsetHeight - innerHeight;
    const current = openingProgress(
      -section.getBoundingClientRect().top,
      range,
    );
    const next = Math.min(
      chapters.length,
      Math.floor(current.plate + 0.03) + 1,
    );
    const target =
      next >= chapters.length
        ? range
        : range * (next / (chapters.length - 1)) * 0.72;
    scrollTo({
      top: section.getBoundingClientRect().top + scrollY + target,
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
    });
  }

  return (
    <section
      className="depth-opening"
      ref={root}
      aria-label="ChequeVerify evidence gallery"
    >
      <div className="depth-stage" ref={stage}>
        <div className="depth-space" aria-hidden="true">
          {chapters.map((item, index) => {
            const sample = labSamples[item.sample],
              base = sample.responses.baseline.result,
              athn = sample.responses.proposed.result;
            const width = base.model_input_shape.at(-1)!,
              height = base.model_input_shape.at(-2)!;
            return (
              <article
                key={item.label}
                ref={(el) => {
                  plates.current[index] = el;
                }}
                className={`depth-plate frame-${index}`}
                style={{ "--frame-accent": item.accent } as React.CSSProperties}
              >
                <header className="depth-plate-brand">
                  <span>
                    <img
                      src="/brand/mark-3d.png"
                      width="40"
                      height="44"
                      alt=""
                    />{" "}
                    ChequeVerify
                  </span>
                  <small>
                    RECORDED DEV STUDY <i />{" "}
                    {String(index + 1).padStart(2, "0")} / 06
                  </small>
                </header>
                <div className="depth-plate-heading">
                  <span>{item.label}</span>
                  <h2>{item.title}</h2>
                </div>
                <div className="depth-specimen-body">
                  <div className="depth-crop-stage">
                    <div className="depth-crop-meta">
                      <ScanLine size={17} />
                      <span>
                        {sample.synthetic
                          ? "SYNTHETIC FIELD"
                          : "GENUINE HANDWRITING"}
                      </span>
                      <strong>
                        {width} × {height} px
                      </strong>
                    </div>
                    <div className="depth-source-pixels">
                      <img
                        src={sample.image}
                        alt=""
                        style={{
                          imageRendering: width < 40 ? "pixelated" : "auto",
                        }}
                        loading="eager"
                        fetchPriority={index === 0 ? "high" : "auto"}
                      />
                      <span className="depth-scan-line" />
                      <svg
                        className="depth-crop-corners"
                        viewBox="0 0 600 300"
                        preserveAspectRatio="none"
                      >
                        <path
                          d="M15 50V15h35M550 15h35v35M585 250v35h-35M50 285H15v-35"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        />
                      </svg>
                    </div>
                    <div className="depth-input-dimensions">
                      <span>
                        BASELINE INPUT{" "}
                        <b>
                          {width} × {height}
                        </b>
                      </span>
                      <ArrowUpRight size={20} />
                      <span>
                        ATHN INPUT{" "}
                        <b>
                          {athn.model_input_shape.at(-1)} ×{" "}
                          {athn.model_input_shape.at(-2)}
                        </b>
                      </span>
                    </div>
                  </div>
                  <div className="depth-reading-rail">
                    <div>
                      <span>BASELINE / RAW READING</span>
                      <strong
                        className={base.raw_text.length > 10 ? "long" : ""}
                      >
                        {base.raw_text || "(empty)"}
                      </strong>
                      <small>
                        Parsed value <b>{base.parsed_value ?? "Not parsed"}</b>
                      </small>
                    </div>
                    <div className="depth-reading-athn">
                      <span>WITH ATHN / RAW READING</span>
                      <strong
                        className={athn.raw_text.length > 10 ? "long" : ""}
                      >
                        {athn.raw_text || "(empty)"}
                      </strong>
                      <small>
                        Parsed value <b>{athn.parsed_value ?? "Not parsed"}</b>
                      </small>
                    </div>
                  </div>
                </div>
                <footer className="depth-plate-foot">
                  <span>Same recogniser · Original pixels magnified</span>
                  <span>
                    {sample.synthetic ? "Synthetic" : "Handwritten"} · DEV
                    demonstration
                  </span>
                </footer>
              </article>
            );
          })}
        </div>
        <button
          className="depth-scroll-cue"
          onClick={forward}
          aria-label="Scroll forward through the introduction"
        >
          <span>Scroll</span>
          <ArrowDown size={15} aria-hidden="true" />
        </button>
        <div className="sr-only">
          Six specimen frames use actual development inputs and saved backend
          readings. These are not accuracy claims. Scrolling moves through the
          evidence, then dissolves into the site. The leaflet is a separate
          research publication.
        </div>
      </div>
    </section>
  );
}
