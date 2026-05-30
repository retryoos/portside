import type { ReactNode } from "react";

// The single horizontal container for the marketing site. Caps content at
// 1240px (matches the app's max layout width) and pads the gutters at the
// design-token horizontal rhythm.
export default function Container({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto w-full max-w-[1240px] px-6 md:px-10 ${className}`}>
      {children}
    </div>
  );
}
