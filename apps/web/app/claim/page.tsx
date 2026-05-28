import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import ClaimLetter, { LETTER_DOM_ID } from "@/components/ClaimLetter";
import ExportPdfButton from "@/components/ExportPdfButton";
import SourcesTabs from "@/components/SourcesTabs";
import TimebarBadge from "@/components/TimebarBadge";

// SCREEN 2 — Claim view (DESIGN.md §Screens 2). Breadcrumb + amber time-bar
// countdown + ONE ink primary "Send to charterer"; two columns — LEFT (~58%) the
// formal letter, RIGHT (~42%) Sources / Calculation / Documents tabs. Client-side
// PDF export. Data: lib/demo.ts (demoVoyage).
export default function ClaimViewPage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Voyages", "MT Aegean Pioneer", "Claim"]} />

      <main className="mx-auto max-w-[1200px] px-8 py-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span aria-hidden="true" className="inline-block h-2 w-2 rounded-sm bg-accent" />
            <h1 className="text-h1 text-primary">
              MT Aegean Pioneer — Ras Tanura / Rotterdam
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <TimebarBadge />
            <ExportPdfButton targetId={LETTER_DOM_ID} />
            <button
              type="button"
              className="rounded-sm bg-cta px-4 py-2.5 text-body-sm text-on-cta transition-colors hover:bg-cta-hover"
            >
              Send to charterer
            </button>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-[58fr_42fr]">
          <div>
            <ClaimLetter />
          </div>
          <div>
            <SourcesTabs />
          </div>
        </div>
      </main>
    </div>
  );
}
