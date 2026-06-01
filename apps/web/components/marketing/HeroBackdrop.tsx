"use client";

import { useEffect, useRef } from "react";

// "Living ink": three deep maritime-ink blobs drifting on long CSS loops over
// the near-black hero base, finished with a fine grain layer and a vignette so
// the headline always reads. A tamed pointer + scroll parallax shifts each
// depth layer by a few px (background slower than foreground) for a spatial
// nod, never a gimmick. All motion is disabled under prefers-reduced-motion;
// the static composition (blobs at rest, grain, vignette) still looks finished.
export default function HeroBackdrop() {
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    if (
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      return;
    }

    // Targets and current values, eased toward each frame so the parallax
    // glides rather than snaps. Pointer is normalised to [-1, 1] from centre.
    let targetX = 0;
    let targetY = 0;
    let curX = 0;
    let curY = 0;
    let scrollY = 0;
    let raf = 0;

    const onPointer = (event: PointerEvent) => {
      const { innerWidth, innerHeight } = window;
      targetX = (event.clientX / innerWidth - 0.5) * 2;
      targetY = (event.clientY / innerHeight - 0.5) * 2;
    };
    const onScroll = () => {
      scrollY = window.scrollY;
    };

    const tick = () => {
      curX += (targetX - curX) * 0.06;
      curY += (targetY - curY) * 0.06;
      root.style.setProperty("--px", curX.toFixed(4));
      root.style.setProperty("--py", curY.toFixed(4));
      root.style.setProperty("--sy", scrollY.toFixed(1));
      raf = requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", onPointer, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    raf = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("pointermove", onPointer);
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div
      ref={rootRef}
      aria-hidden="true"
      className="hero-ink absolute inset-0 overflow-hidden"
      style={{ ["--px" as string]: 0, ["--py" as string]: 0, ["--sy" as string]: 0 }}
    >
      {/* Three depth layers. Each drifts on its own long loop; parallax depth
          (data-depth) scales how far pointer/scroll nudge it. */}
      <span className="hero-ink-blob hero-ink-blob--a" data-depth="1" />
      <span className="hero-ink-blob hero-ink-blob--b" data-depth="2" />
      <span className="hero-ink-blob hero-ink-blob--c" data-depth="3" />
      {/* Fine grain to kill banding on the soft gradients. */}
      <span className="hero-ink-grain" />
      {/* Vignette: pulls the corners down so the editorial headline stays the
          brightest thing on the canvas. */}
      <span className="hero-ink-vignette" />
    </div>
  );
}
