import Link from "next/link";
import Container from "./Container";

// Marketing hero. Full-bleed deep-ink surface (so it works without a
// committed photograph), an optional hero photograph behind a diagonal
// ink scrim, and an asymmetric content block: eyebrow + huge editorial
// headline + body + two pills on the left, breathing space on the right.
//
// Once a real photograph lands at /photography/hero-landing.jpg the
// background-image kicks in and the deep-ink base shows through the scrim.
export default function Hero() {
  return (
    <section className="relative isolate min-h-[100vh] overflow-hidden bg-primary text-on-primary">
      {/* Photograph layer, falls back to bg-primary if the asset is missing. */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center opacity-70"
        style={{ backgroundImage: "url('/photography/hero-landing.jpg')" }}
      />
      {/* Diagonal scrim so the headline always reads. */}
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 60%, rgba(0,0,0,0) 100%)",
        }}
      />

      <div className="relative flex min-h-[100vh] flex-col justify-end pb-16 pt-32 md:pb-24 md:pt-40">
        <Container>
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-[1.4fr_1fr] lg:gap-16">
            <div className="max-w-2xl">
              <p className="text-eyebrow text-on-primary/80">
                AI for maritime operations
              </p>
              <h1 className="text-hero mt-6 text-on-primary">
                AI workflows for maritime operations.
              </h1>
              <p className="mt-7 max-w-xl text-body-lg text-on-primary/85">
                Starting with the claims that used to take days. Three voyage
                documents in, a finished, cited demurrage claim out, in under a
                minute. Built for ship owners, charterers, and the lawyers who
                file their claims.
              </p>
              <div className="mt-10 flex flex-wrap items-center gap-4">
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

            {/* The asymmetric trust panel: a small glass card that sits over
                the photograph and carries one social-proof line. */}
            <div className="hidden lg:flex lg:items-end lg:justify-end">
              <div className="card-glass max-w-sm px-7 py-7 text-primary">
                <p className="text-eyebrow text-secondary">
                  Trusted approach
                </p>
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
    </section>
  );
}
