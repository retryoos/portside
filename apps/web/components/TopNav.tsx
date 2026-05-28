import Link from "next/link";

// Top app bar (DESIGN.md "Layout"): serif "Portside" wordmark + nav. Shared
// chrome across all screens. Foundation-owned — screen subagents import, not edit.
const NAV = [
  { label: "Dashboard", href: "/" },
  { label: "Claims", href: "/claim" },
  { label: "Vessels", href: "/" },
  { label: "Reports", href: "/" },
];

export default function TopNav() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-neutral px-8 py-4">
      <div className="flex items-center gap-10">
        <Link href="/" className="text-h2 text-primary">
          Portside
        </Link>
        <nav className="hidden items-center gap-7 md:flex">
          {NAV.map((item, i) => (
            <Link
              key={`${item.label}-${i}`}
              href={item.href}
              className="text-body-sm text-secondary transition-colors hover:text-primary"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="text-label-caps text-secondary">Claims desk</div>
    </header>
  );
}
