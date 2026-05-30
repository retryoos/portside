import BackArrowButton from "@/components/BackArrowButton";
import TopNav from "@/components/TopNav";
import ReviseLetter from "@/components/ReviseLetter";

// SCREEN 3: Inline highlight-and-revise (DESIGN.md §Screens 3,
// notes/13-inline-revision.md). Full-width letter (~820px); a client-side mock of
// the highlight-and-revise interaction. No backend revise endpoint in scope.
export default function RevisePage() {
  return (
    <div className="min-h-screen pt-16">
      <TopNav />
      <div className="mx-auto max-w-[820px] px-8 pt-6">
        <BackArrowButton href="/cases" />
      </div>
      <main className="mx-auto max-w-[820px] px-8 py-10">
        <ReviseLetter />
      </main>
    </div>
  );
}
