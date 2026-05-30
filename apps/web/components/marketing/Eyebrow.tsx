import type { ReactNode } from "react";

// The small label every marketing section opens with. Inherits text colour
// from its parent so it sits well on both neutral and inverse grounds.
export default function Eyebrow({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <p className={`text-eyebrow ${className}`}>{children}</p>;
}
