// Tiny crossfade wrapper used by the claim detail page to fade real content
// in over its skeleton placeholder. 300ms opacity + 4px slide-up; no state.
import type { ReactNode } from "react";

export default function Reveal({
  ready,
  children,
}: {
  ready: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`transition-all duration-300 ease-out ${
        ready ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"
      }`}
    >
      {children}
    </div>
  );
}
