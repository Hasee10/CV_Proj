import { lazy, Suspense, useEffect, useRef } from "react";
import { ArrowDown, ArrowUpRight, ScanLine } from "lucide-react";
import { labSamples } from "../../lib/sampleLibrary";
import { ease, nextOpeningStop, openingPose, openingProgress, specimenVisibility,
  type OpeningSceneState } from "./openingMotion";
export { openingProgress, specimenVisibility } from "./openingMotion";
const OpeningBrandScene = lazy(() => import("./OpeningBrandScene"));

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

export function EntryExperience({ onEnter }: { onEnter: () => void }) {
  const root = useRef<HTMLElement>(null),
    stage = useRef<HTMLDivElement>(null);
  const plates = useRef<(HTMLElement | null)[]>([]),
    enter = useRef(onEnter);
  const wake = useRef<() => void>(() => {});
  const sceneState = useRef<OpeningSceneState>({
    phase: 0, logoOpacity: 0, reduced: false,
    anchor: { x: 0, y: 0, height: 39 }, siteAnchor: { x: 0, y: 0, height: 44 },
  });
  const fallback = useRef<HTMLImageElement>(null);
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
      const pose = openingPose(phase, reduced.matches);
      const first = Math.floor(plate),
        weight = plate - first;
      const a = chapters[first].color,
        b = chapters[Math.min(chapters.length - 1, first + 1)].color;
      stage.current!.style.backgroundColor = `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * weight)).join(",")})`;
      stage.current!.style.opacity = String(1 - dissolve);
      stage.current!.dataset.openingPhase = phase < 0.375 ? "identity" : "evidence";
      let logoOpacity = 0;
      let anchor = sceneState.current.anchor;

      plates.current.forEach((image, index) => {
        if (!image) return;
        const delta = index - plate;
        const direction = chapters[index].side;
        const opacity = specimenVisibility(index, plate, reduced.matches) * pose.gallery;
        image.style.opacity = String(opacity);
        image.style.visibility = opacity > 0.001 ? "visible" : "hidden";
        image.style.transform = reduced.matches
          ? "translate(-50%, -50%)"
          : `translate3d(calc(-50% + ${delta * 14 * direction}vw), calc(-50% + ${delta * 2 - dissolve * 1.5 + (1 - pose.gallery) * 4}vh), ${-delta * 240 + dissolve * 70}px) rotateY(${-delta * 7 * direction}deg)`;
        image.dataset.visible = opacity > 0.001 ? "true" : "false";
        image.style.zIndex = String(10 - index);
        if ((index === 0 && phase < 0.39) || opacity > 0.001) {
          const rect = image.querySelector(".depth-plate-brand img")!.getBoundingClientRect();
          anchor = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, height: rect.height };
          logoOpacity = opacity;
        }
      });
      const siteRect = document.querySelector(".vision-header .brand-mark")?.getBoundingClientRect();
      sceneState.current = {
        phase, anchor, logoOpacity, reduced: reduced.matches,
        siteAnchor: siteRect ? { x: siteRect.left + siteRect.width / 2,
          y: siteRect.top + siteRect.height / 2, height: siteRect.height } : anchor,
      };
      // A real brand render remains available while WebGL loads or is unavailable.
      const image = fallback.current!;
      const logoSize = Math.min(innerWidth * 0.52, innerHeight * 0.4, 340);
      const mix = (a: number, b: number) => a + (b - a) * pose.dock;
      image.style.left = `${mix(innerWidth / 2, anchor.x)}px`;
      image.style.top = `${mix(innerHeight / 2, anchor.y)}px`;
      image.style.width = `${mix(logoSize, anchor.height)}px`;
      image.style.height = image.style.width;
      image.style.opacity = String(phase < 0.375
        ? reduced.matches ? 1 : ease((phase - .06) / .09)
        : logoOpacity);
      wake.current();
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
    const target = range * nextOpeningStop(current.phase);
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
        <div className="opening-fallback-ribbons" aria-hidden="true"><i /><i /><i /></div>
        <img className="opening-brand-fallback" ref={fallback} src="/brand/mark-3d.png" alt="" aria-hidden="true" />
        <Suspense fallback={null}><OpeningBrandScene state={sceneState} wake={wake} /></Suspense>
        <div className="depth-space">
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
          The introduction opens with sliding ribbons and our particle logo,
          which becomes solid and moves into the first specimen header.
        </div>
      </div>
    </section>
  );
}
