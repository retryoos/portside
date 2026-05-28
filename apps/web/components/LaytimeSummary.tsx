// Laytime calculation summary block on surface-muted (DESIGN.md §Screens 2,
// notes/06-frontend.md §5 quantum). Allowed / used / on demurrage / rate / due.
import { demoVoyage } from "@/lib/demo";
import { formatHours, formatEur } from "@/lib/format";
import type { LaytimeResult } from "@/lib/types";

export default function LaytimeSummary({
  laytime = demoVoyage.laytime,
}: {
  laytime?: LaytimeResult | null;
}) {
  const lt = laytime;
  if (!lt) return null;

  const rows: { label: string; value: string }[] = [
    { label: "Laytime allowed", value: `${formatHours(lt.laytime_allowed_hours)} h` },
    { label: "Laytime used", value: `${formatHours(lt.laytime_used_hours)} h` },
    { label: "On demurrage", value: `${formatHours(lt.time_on_demurrage_hours)} h` },
    { label: "Demurrage rate", value: `${formatEur(lt.demurrage_rate_per_hour_eur)}/h` },
  ];

  return (
    <div className="rounded-lg bg-surface-muted p-5">
      <p className="text-label-caps text-secondary">Calculation summary</p>
      <dl className="mt-4 divide-y divide-border">
        {rows.map((r) => (
          <div key={r.label} className="flex items-baseline justify-between py-2">
            <dt className="text-body-sm text-secondary">{r.label}</dt>
            <dd className="text-body-sm text-primary">{r.value}</dd>
          </div>
        ))}
        <div className="flex items-baseline justify-between pt-3">
          <dt className="text-h3 text-primary">Demurrage due</dt>
          <dd className="text-h3 text-primary">{formatEur(lt.demurrage_due_eur)}</dd>
        </div>
      </dl>
    </div>
  );
}
