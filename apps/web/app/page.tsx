import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import CaseHeader from "@/components/CaseHeader";
import CorrespondenceTimeline from "@/components/CorrespondenceTimeline";
import OutcomeTable from "@/components/OutcomeTable";
import { demoCorrespondence, demoOutcome } from "@/lib/demo";

// SCREEN 1 — Case detail / settled (DESIGN.md §Screens 1). Serif case title +
// settlement subline; vertical dispute-correspondence timeline; an Outcome table.
export default function CaseDetailPage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Vessels", "MT Aegean Pioneer", "Settled"]} />
      <main className="mx-auto max-w-[960px] px-8 py-10">
        <CaseHeader
          title="MT Aegean Pioneer — Ras Tanura / Rotterdam"
          settledUsd={demoOutcome.settled_eur}
          daysToSettlement={demoOutcome.days_to_settlement}
        />
        <div className="mt-10">
          <CorrespondenceTimeline items={demoCorrespondence} />
        </div>
        <div className="mt-10">
          <OutcomeTable outcome={demoOutcome} />
        </div>
      </main>
    </div>
  );
}
