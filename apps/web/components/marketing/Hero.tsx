"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Container from "./Container";
import HeroBackdrop from "./HeroBackdrop";

// Marketing hero. A full-bleed deep-ink surface carrying the "living ink"
// animated backdrop, a diagonal scrim for legibility, and an asymmetric
// content block: eyebrow + huge editorial headline + body + two pills on the
// left, a glass trust panel on the right.
//
// The headline arrives as a per-line clip reveal (Linear-style wipe). The
// surrounding elements stage in beneath it. Everything resolves to its final
// static state instantly under prefers-reduced-motion.
export default function Hero() {
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      setShown(true);
      return;
    }
    // Defer one frame so the initial (hidden) state paints before we flip,
    // guaranteeing the transition actually runs.
    const id = requestAnimationFrame(() => setShown(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const state = shown ? "is-shown" : "";

  return (
    <section className="hero-root relative isolate min-h-[100vh] overflow-hidden bg-primary text-on-primary">
      <HeroBackdrop />

      {/* Diagonal scrim so the headline always reads against the moving ink. */}
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.12) 58%, rgba(0,0,0,0) 100%)",
        }}
      />

      <div className="relative flex min-h-[100vh] flex-col justify-end pb-16 pt-32 md:pb-24 md:pt-40">
        <Container>
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
            <div className="max-w-2xl">
              <p
                className={`hero-stage ${state} text-eyebrow text-on-primary/80`}
                style={{ ["--stage-delay" as string]: "60ms" }}
              >
                AI for maritime operations
              </p>

              <h1 className="text-hero mt-6 text-on-primary">
                <span className="hero-line">
                  <span
                    className={`hero-line-inner ${state}`}
                    style={{ ["--stage-delay" as string]: "140ms" }}
                  >
                    AI workflows for
                  </span>
                </span>
                <span className="hero-line">
                  <span
                    className={`hero-line-inner ${state}`}
                    style={{ ["--stage-delay" as string]: "240ms" }}
                  >
                    maritime operations.
                  </span>
                </span>
              </h1>

              <p
                className={`hero-stage ${state} mt-7 max-w-xl text-body-lg text-on-primary/85`}
                style={{ ["--stage-delay" as string]: "360ms" }}
              >
                Starting with the claims that used to take days. Three voyage
                documents in, a finished, cited demurrage claim out, in under a
                minute. Built for ship owners, charterers, and the lawyers who
                file their claims.
              </p>

              <div
                className={`hero-stage ${state} mt-10 flex flex-wrap items-center gap-4`}
                style={{ ["--stage-delay" as string]: "460ms" }}
              >
                <Link
                  href="/contact"
                  className="btn-lift rounded-pill bg-cta-inverse px-6 py-3 text-body-sm font-semibold text-on-cta-inverse hover:bg-cta-inverse-hover"
                >
                  Book a demo
                </Link>
                <Link
                  href="#product"
                  className="btn-lift rounded-pill border border-on-primary/30 px-6 py-3 text-body-sm font-semibold text-on-primary hover:bg-on-primary/10"
                >
                  See the product
                </Link>
              </div>
            </div>

            {/* The asymmetric trust panel: a glass card over the moving ink,
                carrying one social-proof line. Floats up last. */}
            <div className="hidden lg:flex lg:items-end lg:justify-end">
              <div
                className={`hero-stage hero-card ${state} card-glass max-w-sm px-7 py-7 text-primary`}
                style={{ ["--stage-delay" as string]: "560ms" }}
              >
                <p className="text-eyebrow text-secondary">Trusted approach</p>
                <p className="mt-4 text-h3 text-primary">
                  Every figure cited. Every claim auditable.
                </p>
                <p className="mt-4 text-body-sm text-secondary">
                  Deterministic arithmetic, clause-by-clause citations, and the
                  90-day time bar tracked on every voyage.
                </p>
              </div>
            </div>
          </div>
        </Container>
      </div>

      {/* Scroll cue. Fades in once the entrance settles, gently bobs. */}
      <div
        className={`hero-stage ${state} pointer-events-none absolute inset-x-0 bottom-6 flex justify-center`}
        style={{ ["--stage-delay" as string]: "760ms" }}
      >
        <span className="hero-scroll-cue text-label-caps text-on-primary/50">
          Scroll
        </span>
      </div>
    </section>
  );
}
