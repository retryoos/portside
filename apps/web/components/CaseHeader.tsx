import { formatEur } from "@/lib/format";

// Screen 1 case header (DESIGN.md §Screens 1). Serif title + settlement subline.
// At most ONE small amber accent dot beside the title (the single sanctioned
// decorative use of accent per header).
export default function CaseHeader({
  title,
  settledUsd,
  daysToSettlement,
}: {
  title: string;
  settledUsd: number;
  daysToSettlement: number;
}) {
  return (
    <header>
      <div className="flex items-center gap-3">
        <h1 className="text-h1 text-primary">{title}</h1>
        <span
          aria-hidden
          className="inline-block h-2 w-2 shrink-0 rounded-full bg-accent"
        />
      </div>
      <p className="mt-2 text-body text-secondary">
        Settled at {formatEur(settledUsd)} — {daysToSettlement} days from claim
        submission
      </p>
    </header>
  );
}
