import type { CorrespondenceItem } from "@/lib/demo";
import { formatDate } from "@/lib/format";
import StatusBadge from "@/components/StatusBadge";

// Screen 1 dispute correspondence timeline (DESIGN.md §Screens 1, timeline-item).
// Date in secondary on the left, actor + summary on a white card on the right.
// "Detected from inbox" badge marks auto-assembled correspondence; the settled
// item gets the one sanctioned 3px green left border + a green check.
export default function CorrespondenceTimeline({
  items,
}: {
  items: CorrespondenceItem[];
}) {
  return (
    <section>
      <h2 className="text-label-caps uppercase text-secondary">
        Dispute timeline
      </h2>
      <ol className="mt-4 flex flex-col gap-4">
        {items.map((item, i) => (
          <li key={`${item.date}-${i}`} className="flex gap-5">
            <time className="w-24 shrink-0 pt-5 text-body-sm text-secondary">
              {formatDate(item.date)}
            </time>
            <div
              className={`flex-1 rounded-md border border-border bg-surface p-5 ${
                item.settled ? "border-l-[3px] border-l-success" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-h3 text-primary">{item.actor}</p>
                <div className="flex shrink-0 items-center gap-2">
                  {item.detectedFromInbox && (
                    <StatusBadge variant="warning">
                      Detected from inbox
                    </StatusBadge>
                  )}
                  {item.settled && (
                    <span
                      aria-label="Settled"
                      className="text-base leading-none text-success"
                    >
                      ✓
                    </span>
                  )}
                </div>
              </div>
              <p className="mt-1.5 text-body text-secondary">{item.summary}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
