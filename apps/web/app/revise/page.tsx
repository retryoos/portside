import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";

// SCREEN 3 — Inline highlight-and-revise (DESIGN.md §Screens 3, notes/13-inline-revision.md).
// STUB — built by the Screen-1/3 subagent. Build: full-width formal letter; a
// floating quick-prompt ("Make the weather argument stronger and cite The Mexico
// 1"); the old sentence struck through in danger color; the replacement paragraph
// in a revise-highlight amber block (contested-container) citing The Mexico 1
// [1990] 1 Lloyd's Rep 507 + Rotterdam Port Authority precipitation data; an
// Accept / Reject control (Accept = ink primary, Reject = ghost). This is a
// client-side mock (no backend revise endpoint in scope). Keep TopNav + Breadcrumb.
// Data: lib/demo.ts (demoVoyage.packet.claim_letter_markdown).
export default function RevisePage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Voyages", "MT Aegean Pioneer", "Claim", "Refine"]} />
      <main className="mx-auto max-w-[820px] px-8 py-10">
        <h1 className="text-h1 text-primary">Refine the letter</h1>
        <p className="mt-2 text-body text-secondary">Inline revise screen — to be built.</p>
      </main>
    </div>
  );
}
