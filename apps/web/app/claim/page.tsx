import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";

// SCREEN 2 — Claim view (DESIGN.md §Screens 2). STUB — built by the Screen-2
// subagent. Build: breadcrumb + amber time-bar countdown + one ink primary
// "Send to charterer"; two columns — LEFT (~58%) the formal letter ("TO:
// CHARTERERS", serif hero figure "Demurrage due to owners: USD 84,375.00" in
// text-hero-figure, letter body in text-letter-body); RIGHT (~42%) a panel with
// Sources / Calculation / Documents tabs showing the laytime summary block + the
// SoF/laytime table (TIMESTAMP / DESCRIPTION / CATEGORY / CUM. HRS, contested row
// amber). Client-side PDF export. Keep TopNav + Breadcrumb. Data: lib/demo.ts
// (demoVoyage).
export default function ClaimViewPage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Voyages", "MT Aegean Pioneer", "Claim"]} />
      <main className="mx-auto max-w-[1100px] px-8 py-10">
        <h1 className="text-h1 text-primary">Claim view</h1>
        <p className="mt-2 text-body text-secondary">Claim view screen — to be built.</p>
      </main>
    </div>
  );
}
