import type { Metadata } from "next";
import Link from "next/link";
import Section from "@/components/marketing/Section";
import ContactForm from "@/components/marketing/ContactForm";

export const metadata: Metadata = {
  title: "Contact · Laytimely",
  description:
    "Get in touch with the Laytimely team. Sales, support, security, and press.",
};

const CHANNELS: {
  eyebrow: string;
  title: string;
  body: string;
  email: string;
}[] = [
  {
    eyebrow: "Sales",
    title: "Book a demo.",
    body: "We will walk you through a live run on real voyage documents and answer questions on the pipeline, the trust model, and pricing.",
    email: "sales@laytimely.com",
  },
  {
    eyebrow: "Support",
    title: "Talk to a human.",
    body: "Existing customers reach the on-call team here. Most replies within a couple of hours during European business hours.",
    email: "support@laytimely.com",
  },
  {
    eyebrow: "Security",
    title: "Report a vulnerability.",
    body: "Suspected vulnerabilities, abuse, and incident reports. Acknowledged within one business day.",
    email: "security@laytimely.com",
  },
  {
    eyebrow: "Press",
    title: "Talk to the founders.",
    body: "Journalists and analysts: brief notes are welcome and we keep embargoed details in confidence.",
    email: "press@laytimely.com",
  },
];

export default function ContactPage() {
  return (
    <main className="pt-24">
      <Section>
        <p className="text-eyebrow text-secondary">Contact</p>
        <h1 className="text-display mt-6 max-w-3xl text-primary">
          Get in touch.
        </h1>
        <p className="mt-6 max-w-2xl text-body-lg text-secondary">
          The team reads every message. Send a note below, or use one of the
          direct channels that matches your question.
        </p>

        <div className="mt-16 max-w-2xl">
          <ContactForm />
        </div>

        <p className="mt-20 text-eyebrow text-secondary">Direct channels</p>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          {CHANNELS.map((c) => (
            <div
              key={c.email}
              className="rounded-card border border-border bg-surface p-8"
            >
              <p className="text-eyebrow text-secondary">{c.eyebrow}</p>
              <p className="mt-4 text-h2 text-primary">{c.title}</p>
              <p className="mt-4 text-body text-secondary">{c.body}</p>
              <Link
                href={`mailto:${c.email}`}
                className="btn-lift mt-7 inline-flex rounded-pill bg-cta px-5 py-2.5 text-body-sm font-semibold text-on-cta hover:bg-cta-hover"
              >
                {c.email}
              </Link>
            </div>
          ))}
        </div>
      </Section>
    </main>
  );
}
