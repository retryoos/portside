// Amber time-bar countdown chip (DESIGN.md "Confidence display" / badge-warning).
// >30 days = success (green), 1-30 = warning (amber), <=0 = danger (red).
import { demoVoyage } from "@/lib/demo";

export default function TimebarBadge() {
  const days = demoVoyage.packet?.days_until_time_bar ?? 0;

  const tone =
    days > 30
      ? "bg-success-container text-success"
      : days > 0
        ? "bg-warning-container text-warning"
        : "bg-danger-container text-danger";

  return (
    <span
      className={`inline-flex items-center rounded-sm px-2.5 py-1 text-label-caps ${tone}`}
    >
      Time bar: {days} {days === 1 ? "day" : "days"}
    </span>
  );
}
