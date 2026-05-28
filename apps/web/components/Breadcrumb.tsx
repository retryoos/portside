// Breadcrumb row under the top app bar (DESIGN.md "Layout"). Shared chrome.

export default function Breadcrumb({ segments }: { segments: string[] }) {
  return (
    <nav className="border-b border-border bg-neutral px-6 py-2.5 md:px-8">
      <ol className="mx-auto flex max-w-[1200px] items-center gap-2 text-label-caps text-secondary">
        {segments.map((seg, i) => (
          <li key={`${seg}-${i}`} className="flex items-center gap-2">
            {i > 0 && (
              <span aria-hidden="true" className="text-border">
                /
              </span>
            )}
            <span className={i === segments.length - 1 ? "text-primary" : ""}>
              {seg}
            </span>
          </li>
        ))}
      </ol>
    </nav>
  );
}
