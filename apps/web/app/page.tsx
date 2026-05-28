import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";

// SCREEN 1 — Case detail / settled (DESIGN.md §Screens 1). STUB — built by the
// Screen-1/3 subagent. Build: serif case title ("MT Aegean Pioneer — Ras Tanura
// / Rotterdam", "Settled at USD 79,000 — 21 days from claim submission"); a
// vertical dispute-correspondence timeline (demoCorrespondence, "Detected from
// inbox" badge, green settled item); an Outcome table (demoOutcome). Keep TopNav
// + Breadcrumb. Data: lib/demo.ts (demoCorrespondence, demoOutcome, demoVoyage).
export default function CaseDetailPage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Vessels", "MT Aegean Pioneer", "Settled"]} />
      <main className="mx-auto max-w-[960px] px-8 py-10">
        <h1 className="text-h1 text-primary">MT Aegean Pioneer — Ras Tanura / Rotterdam</h1>
        <p className="mt-2 text-body text-secondary">Case detail screen — to be built.</p>
      </main>
    </div>
  );
}
