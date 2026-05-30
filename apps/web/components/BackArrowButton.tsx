// Floating circular back button for detail pages. Pure white surface with a
// thin border-strong hairline; the global focus-visible ring covers focus.

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
      className="inline-flex h-10 w-10 items-center justify-center rounded-pill border border-border-strong bg-surface text-primary transition-colors hover:bg-surface-muted"
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
