import type { ReactNode } from "react";
import Container from "./Container";

type Tone = "neutral" | "inverse" | "muted";

// The vertical rhythm primitive for the marketing site. Variants control
// the background tone; the height stays consistent so scroll cadence reads
// as deliberate. The `id` attribute supports anchor navigation from the
// MarketingNav.
export default function Section({
  id,
  tone = "neutral",
  children,
  className = "",
  contained = true,
}: {
  id?: string;
  tone?: Tone;
  children: ReactNode;
  className?: string;
  /** When false, the children render full-bleed and own their own container. */
  contained?: boolean;
}) {
  const toneClass =
    tone === "inverse"
      ? "bg-primary text-on-primary"
      : tone === "muted"
        ? "bg-surface-muted text-primary"
        : "bg-neutral text-primary";

  return (
    <section
      id={id}
      className={`relative overflow-hidden py-24 md:py-32 ${toneClass} ${className}`}
    >
      {contained ? <Container>{children}</Container> : children}
    </section>
  );
}
