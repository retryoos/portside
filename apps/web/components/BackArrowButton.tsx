// Floating circular back button for detail pages. Glass-styled (bg-surface
// picks up the global frosted-glass treatment from globals.css), with a
// centred chevron-left icon. Placed in the page content top-left area, not
// inside the TopNav.

import Link from "next/link";

interface BackArrowButtonProps {
  /** Parent route to navigate to. */
  href: string;
}

export default function BackArrowButton({ href }: BackArrowButtonProps) {
  return (
    <Link
      href={href}
      aria-label="Back"
      className="flex h-11 w-11 items-center justify-center rounded-full border border-border bg-surface text-primary shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-colors hover:bg-surface-muted"
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 16 16"
        className="h-4 w-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M10 4 L6 8 L10 12" />
      </svg>
    </Link>
  );
}
