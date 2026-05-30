// Amber time-bar countdown chip (DESIGN.md "Confidence display" / badge-warning).
// >30 days = success (green), 1-30 = warning (amber), <=0 = danger (red).
import { demoVoyage } from "@/lib/demo";

export default function TimebarBadge({
  days = demoVoyage.packet?.days_until_time_bar ?? 0,
}: {
  days?: number;
}) {

  const tone =
    days > 30
      ? "border-success/30 bg-success-container text-success"
      : days > 0
        ? "border-warning/30 bg-warning-container text-warning"
        : "border-danger/30 bg-danger-container text-danger";

  return (
    <span
      className={`inline-flex items-center rounded-pill border px-3 py-1 text-label-caps ${tone}`}
    >
      Time bar: {days} {days === 1 ? "day" : "days"}
    </span>
  );
}
