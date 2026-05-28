// Shared formatters. DESIGN.md: money "USD 84,375.00"; timestamps "17 May 14:00 LT";
// confidence shown as a WORD (Strong/Arguable/Weak), never a numeric percentage.

export function formatUsd(amount: number): string {
  return `USD ${amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function formatHours(hours: number): string {
  return hours.toLocaleString("en-US", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

/** "2026-05-17T14:00:00+02:00" -> "17 May 14:00 LT" (preserves the wire offset). */
export function formatLocalTimestamp(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!m) return iso;
  const [, , month, day, hh, mm] = m;
  return `${day} ${MONTHS[parseInt(month, 10) - 1] ?? month} ${hh}:${mm} LT`;
}

/** "2026-05-17T14:00:00+02:00" -> "17 May 2026". */
export function formatDate(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return iso;
  const [, year, month, day] = m;
  return `${day} ${MONTHS[parseInt(month, 10) - 1] ?? month} ${year}`;
}

/** Map owner_position_strength (0..1) to a word. No numeric percentages in the UI. */
export function confidenceWord(strength: number): "Strong" | "Arguable" | "Weak" {
  if (strength >= 0.7) return "Strong";
  if (strength >= 0.4) return "Arguable";
  return "Weak";
}
