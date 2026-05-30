import Link from "next/link";
import Container from "./Container";

// The reusable "second-chance" CTA strip that closes the long-form page (and
// can be re-used inside meta pages later). bg-primary inverse surface with
// a confident editorial headline and two inverse pills.
export default function CTASection() {
  return (
    <section className="bg-primary py-24 text-on-primary md:py-32">
      <Container>
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between md:gap-16">
          <div className="max-w-2xl">
            <p className="text-eyebrow text-on-primary/70">Get started</p>
            <h2 className="text-display mt-6 text-on-primary">
              Stop losing valid claims to deadlines you missed.
            </h2>
            <p className="mt-6 max-w-xl text-body-lg text-on-primary/80">
              See a live run on real voyage documents. We will walk you through
              the agents, the citations, and the exported claim letter.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/contact"
              className="btn-lift rounded-pill bg-cta-inverse px-6 py-3 text-body-sm font-semibold text-on-cta-inverse hover:bg-cta-inverse-hover"
            >
              Book a demo
            </Link>
            <Link
              href="/login"
              className="btn-lift rounded-pill border border-on-primary/30 px-6 py-3 text-body-sm font-semibold text-on-primary hover:bg-on-primary/10"
            >
              Open the app
            </Link>
          </div>
        </div>
      </Container>
    </section>
  );
}
