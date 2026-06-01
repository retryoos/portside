import type { Metadata } from "next";
import Section from "@/components/marketing/Section";

export const metadata: Metadata = {
  title: "Privacy, Laytimely",
  description:
    "What Laytimely collects, how we use it, who we share it with, and the rights you retain over your data.",
};

const SECTIONS: { eyebrow: string; body: string }[] = [
  {
    eyebrow: "Who we are",
    body: "Laytimely is a Greek IKE (Ιδιωτική Κεφαλαιουχική Εταιρεία) registered in Athens. The data controller for the product is Laytimely. Questions about this notice should go to privacy@laytimely.com.",
  },
  {
    eyebrow: "What we collect",
    body: "We collect the voyage documents you upload, the metadata you enter while filing a claim, the account information you provide at sign-up, and the standard server-side logs (IP address, timestamp, request path) needed to operate the service.",
  },
  {
    eyebrow: "Why we collect it",
    body: "We use voyage documents and metadata to produce the claim packet you asked for. We use account information to authenticate you, contact you about service-affecting events, and bill you. We use server logs to keep the service up and to investigate abuse.",
  },
  {
    eyebrow: "Who we share it with",
    body: "Subprocessors: Anthropic for the AI agents, Amazon Web Services for hosting and storage, Sentry for error reporting, and Vercel for delivering the marketing site. We never sell personal data. We share with law enforcement only on a valid legal request and only the minimum required to comply.",
  },
  {
    eyebrow: "How long we keep it",
    body: "Voyage documents and derived claim data are retained for the lifetime of the account. You may delete a voyage at any time from the dashboard. Account deletion removes all associated voyage data within thirty days. Backups roll off after thirty days.",
  },
  {
    eyebrow: "Your rights",
    body: "You may access, correct, export, or delete your data at any time. Email privacy@laytimely.com with a verifiable request and we will respond within thirty days. EEA and UK users have the rights conferred by GDPR; California users have the rights conferred by the CCPA.",
  },
  {
    eyebrow: "Cookies",
    body: "We use a single HttpOnly session cookie for sign-in. We use first-party privacy-friendly analytics (Vercel Web Analytics) that do not set advertising cookies. We do not use third-party tracking or advertising cookies.",
  },
  {
    eyebrow: "Changes",
    body: "We will post any change to this notice on this page and update the effective date. Material changes are sent to your account email.",
  },
];

export default function PrivacyPage() {
  return (
    <main className="pt-24">
      <Section>
        <p className="text-eyebrow text-secondary">Privacy</p>
        <h1 className="text-display mt-6 max-w-3xl text-primary">
          What we collect and what we do with it.
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
