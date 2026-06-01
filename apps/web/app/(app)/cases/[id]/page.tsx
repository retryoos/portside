import TopNav from "@/components/TopNav";
import ClaimScreen from "@/components/ClaimScreen";

// SCREEN 2: Claim view, addressed by /cases/<id> (DESIGN.md §Screens 2). The id
// drives the LIVE pipeline (createVoyage from the dashboard lands here, then
// pollVoyage streams each stage). The reserved id "demo" renders the offline
// lib/demo.ts fixture. Letter, staged progress, and Sources/Calculation/Documents
// tabs all live in <ClaimScreen/>.
export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="min-h-screen pt-16">
      <TopNav />
      <ClaimScreen id={id} />
    </div>
  );
}
