import BackArrowButton from "@/components/BackArrowButton";
import TopNav from "@/components/TopNav";
import ReviseLetter from "@/components/ReviseLetter";

// SCREEN 3: Inline highlight-and-revise (DESIGN.md "Surfaces"). Full-width
// letter; the highlight-and-revise interaction is a client-side mock.
export default function RevisePage() {
  return (
    <div className="min-h-screen pt-20">
      <TopNav />
      <main className="mx-auto max-w-[820px] px-6 pb-24 pt-8 md:px-8 md:pt-12">
        <BackArrowButton href="/cases" />

        <header className="mt-10">
          <p className="text-eyebrow text-secondary">Inline revise</p>
          <h1 className="text-h1 mt-4 text-primary">Refine a sentence.</h1>
          <p className="mt-4 max-w-2xl text-body-lg text-secondary">
            Highlight any line in the claim and ask the agent to rewrite it.
            Quantum and citations are locked.
          </p>
        </header>

        <div className="mt-10">
          <ReviseLetter />
        </div>
      </main>
    </div>
  );
}
