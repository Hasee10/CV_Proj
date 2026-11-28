import { useEffect, useRef } from "react";
import { ArrowDown } from "lucide-react";

const chapters = [
  { src: "/gallery/digits.png", color: [243, 225, 188], side: 1 },
  { src: "/gallery/fields.png", color: [241, 234, 221], side: -1 },
  { src: "/gallery/handwriting.png", color: [224, 218, 239], side: -1 },
  { src: "/gallery/scale.png", color: [226, 216, 237], side: 1 },
  { src: "/gallery/synthetic.png", color: [237, 221, 204], side: -1 },
  { src: "/gallery/review.png", color: [241, 234, 221], side: 1 },
];

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

export function EntryExperience({ onEnter }: { onEnter: () => void }) {
  const root = useRef<HTMLElement>(null),
    stage = useRef<HTMLDivElement>(null);
  const plates = useRef<(HTMLImageElement | null)[]>([]),
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
      stage.current!.style.filter = reduced.matches
        ? "none"
        : `blur(${dissolve * 3}px)`;
      plates.current.forEach((image, index) => {
        if (!image) return;
        const delta = index - plate;
        const direction = chapters[index].side;
        const opacity =
          delta >= 0 ? 1 / (1 + delta * 3) : Math.max(0, 1 + delta * 1.8);
        image.style.opacity = String(opacity * (1 - dissolve));
        image.style.transform = reduced.matches
          ? "translate(-50%, -50%)"
          : `translate3d(calc(-50% + ${delta * 25 * direction}vw), calc(-50% + ${delta * 5}vh), ${-delta * 480 + dissolve * 300}px) rotateY(${-delta * 13 * direction}deg)`;
        image.style.filter = reduced.matches
          ? "none"
          : `blur(${Math.min(8, Math.abs(delta) * 3) + dissolve * 5}px)`;
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
    scrollBy({
      top: innerHeight * 0.85,
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
          {chapters.map((item, index) => (
            <img
              key={item.src}
              ref={(el) => {
                plates.current[index] = el;
              }}
              src={item.src}
              width="1200"
              height="1500"
              alt=""
              loading="eager"
              fetchPriority={index === 0 ? "high" : "auto"}
            />
          ))}
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
          Six evidence plates, including newly captured DEV digit strings, a
          handwritten 7, and synthetic 1737. Original examples include: genuine
          handwritten fields that both parse to 1.00; a synthetic numeric crop
          read as 3003 by baseline and 3083 with ATHN; and the synthetic written
          reading mummisessing that cannot be parsed. These are constructed
          development examples, not accuracy claims.
        </div>
      </div>
    </section>
  );
}
