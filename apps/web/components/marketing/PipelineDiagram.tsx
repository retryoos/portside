// The four-agent pipeline rendered as a labelled card row with hairline
// connectors. SVG icons inline; ScrollReveal handled by the parent section.

const AGENTS: { id: string; title: string; line: string }[] = [
  {
    id: "read",
    title: "Read",
    line: "Extracts the contract, the arrival notice, and the hour-by-hour port log into a clean timeline.",
  },
  {
    id: "calculate",
    title: "Calculate",
    line: "Works out the laytime. The arithmetic runs in plain code, never the model, so the numbers are exact.",
  },
  {
    id: "argue",
    title: "Argue",
    line: "Finds the hours the other side will dispute and builds the legal argument with clause citations.",
  },
  {
    id: "draft",
    title: "Draft",
    line: "Writes the finished claim letter in the standard industry format, ready to send.",
  },
];

export default function PipelineDiagram() {
  return (
    <ol className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
      {AGENTS.map((agent, i) => (
        <li
          key={agent.id}
          className="relative flex flex-col gap-5 rounded-card border border-border bg-surface p-7"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-body-sm font-semibold text-on-primary">
            {i + 1}
          </span>
          <div>
            <p className="text-eyebrow text-secondary">Agent {i + 1}</p>
            <p className="mt-3 text-h2 text-primary">{agent.title}</p>
            <p className="mt-4 text-body text-secondary">{agent.line}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
