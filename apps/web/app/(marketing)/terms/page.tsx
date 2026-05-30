import type { Metadata } from "next";
import Section from "@/components/marketing/Section";

export const metadata: Metadata = {
  title: "Terms · Laytimely",
  description:
    "The contract between you and Laytimely for use of the demurrage claims service.",
};

const SECTIONS: { eyebrow: string; body: string }[] = [
  {
    eyebrow: "Agreement",
    body: "By creating an account or using the Laytimely service you agree to these terms. If you are using the service on behalf of an organisation you represent that you have authority to bind that organisation. If you do not agree, do not use the service.",
  },
  {
    eyebrow: "The service",
    body: "Laytimely provides AI-assisted workflows for maritime claims. Outputs from the service, including draft claim letters and laytime calculations, are produced by AI models and deterministic code. They are tools for licensed professionals and are not a substitute for legal or maritime advice. You remain responsible for any claim you file.",
  },
  {
    eyebrow: "Your account",
    body: "You must keep your credentials confidential and notify us immediately at security@laytimely.com if you suspect they have been compromised. You are responsible for activity that occurs under your account.",
  },
  {
    eyebrow: "Your content",
    body: "You retain all rights in the voyage documents and other content you upload. You grant Laytimely a limited licence to process that content for the sole purpose of providing the service. We do not train shared AI models on your content.",
  },
  {
    eyebrow: "Acceptable use",
    body: "You will not use the service to violate any law, infringe any right, attempt to reverse engineer or scrape the product, or upload content that contains malware or attempts to interfere with the service.",
  },
  {
    eyebrow: "Fees and payment",
    body: "Paid plans are billed in advance on the cadence stated at sign-up. Fees are non-refundable except where required by law. We may change pricing on thirty days written notice; changes take effect at your next renewal.",
  },
  {
    eyebrow: "Termination",
    body: "You may cancel your account at any time from the dashboard. We may suspend or terminate accounts that breach these terms. On termination we delete your content within thirty days, subject to legal retention requirements.",
  },
  {
    eyebrow: "Warranties and liability",
    body: "The service is provided on an as-is basis. To the maximum extent permitted by law, Laytimely's aggregate liability for any claim arising from these terms is limited to the fees paid to us in the twelve months preceding the claim. Nothing in these terms limits liability for gross negligence, wilful misconduct, or any liability that cannot be excluded by law.",
  },
  {
    eyebrow: "Governing law",
    body: "These terms are governed by the laws of Greece. Any dispute will be resolved in the courts of Athens.",
  },
  {
    eyebrow: "Changes",
    body: "We may update these terms from time to time. Material changes will be sent to your account email at least fifteen days before they take effect.",
  },
];

export default function TermsPage() {
  return (
    <main className="pt-24">
      <Section>
        <p className="text-eyebrow text-secondary">Terms</p>
        <h1 className="text-display mt-6 max-w-3xl text-primary">
          The contract between you and Laytimely.
        </h1>
        <p className="mt-6 text-body-sm text-secondary">
          Effective {new Date().toISOString().slice(0, 10)}.
        </p>

        <div className="mt-16 grid grid-cols-1 gap-12 md:grid-cols-[1fr_2.2fr]">
          {SECTIONS.map((s) => (
            <PolicyRow key={s.eyebrow} {...s} />
          ))}
        </div>
      </Section>
    </main>
  );
}

function PolicyRow({ eyebrow, body }: { eyebrow: string; body: string }) {
  return (
    <>
      <p className="text-eyebrow text-secondary">{eyebrow}</p>
      <p className="text-body-lg text-secondary">{body}</p>
    </>
  );
}
