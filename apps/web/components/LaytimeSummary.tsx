// Laytime calculation summary block on surface-muted (DESIGN.md §Screens 2,
// notes/06-frontend.md §5 quantum). Allowed / used / on demurrage / rate / due.
import Reveal from "@/components/Reveal";
import { demoVoyage } from "@/lib/demo";
import { formatHours, formatEur } from "@/lib/format";
import type { LaytimeResult } from "@/lib/types";

export default function LaytimeSummary({
  laytime = demoVoyage.laytime,
  loading = false,
}: {
  laytime?: LaytimeResult | null;
  loading?: boolean;
}) {
  if (loading || !laytime) {
    return <LaytimeSummarySkeleton />;
  }

  const lt = laytime;
  const rows: { label: string; value: string }[] = [
    { label: "Laytime allowed", value: `${formatHours(lt.laytime_allowed_hours)} h` },
    { label: "Laytime used", value: `${formatHours(lt.laytime_used_hours)} h` },
    { label: "On demurrage", value: `${formatHours(lt.time_on_demurrage_hours)} h` },
    { label: "Demurrage rate", value: `${formatEur(lt.demurrage_rate_per_hour_eur)}/h` },
  ];

  return (
    <Reveal ready>
      <div className="rounded-md bg-surface-muted p-5">
        <p className="text-eyebrow text-secondary">Calculation summary</p>
        <dl className="mt-5 divide-y divide-border">
          {rows.map((r) => (
            <div key={r.label} className="flex items-baseline justify-between py-2.5">
              <dt className="text-body-sm text-secondary">{r.label}</dt>
              <dd className="text-body-sm tabular-nums text-primary">{r.value}</dd>
            </div>
          ))}
          <div className="flex items-baseline justify-between pt-4">
            <dt className="text-h3 text-primary">Demurrage due</dt>
            <dd className="text-h3 tabular-nums text-primary">
              {formatEur(lt.demurrage_due_eur)}
            </dd>
          </div>
        </dl>
      </div>
    </Reveal>
  );
}

function LaytimeSummarySkeleton() {
  return (
    <div className="rounded-md bg-surface-muted p-5">
      <div className="h-3 w-32 rounded animate-shimmer" />
      <div className="mt-4 divide-y divide-border">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex items-baseline justify-between py-2">
            <div className="h-3 w-24 rounded animate-shimmer" />
            <div className="h-3 w-16 rounded animate-shimmer" />
          </div>
        ))}
        <div className="flex items-baseline justify-between pt-3">
          <div className="h-5 w-32 rounded animate-shimmer" />
          <div className="h-5 w-28 rounded animate-shimmer" />
        </div>
      </div>
    </div>
  );
}
