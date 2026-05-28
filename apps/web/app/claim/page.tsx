import { Suspense } from "react";
import Breadcrumb from "@/components/Breadcrumb";
import TopNav from "@/components/TopNav";
import ClaimScreen from "@/components/ClaimScreen";

// SCREEN 2 — Claim view (DESIGN.md §Screens 2). Runs on the LIVE pipeline when
// the URL carries ?voyage=<id>; otherwise renders the offline demo fixture. The
// dropzone (createVoyage), staged progress (pollVoyage), letter, and Sources/
// Calculation/Documents tabs all live in <ClaimScreen/>. Client-side PDF export.
export default function ClaimViewPage() {
  return (
    <div className="min-h-screen">
      <TopNav />
      <Breadcrumb segments={["Voyages", "MT Aegean Pioneer", "Claim"]} />
      <Suspense fallback={null}>
        <ClaimScreen />
      </Suspense>
    </div>
  );
}
