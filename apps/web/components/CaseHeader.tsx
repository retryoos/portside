import { formatEur } from "@/lib/format";

// Case header: title + settlement subline.
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
      <h1 className="text-h1 text-primary">{title}</h1>
      <p className="mt-2 text-body text-secondary">
        Settled at {formatEur(settledUsd)}, {daysToSettlement} days from claim
        submission
      </p>
    </header>
  );
}
