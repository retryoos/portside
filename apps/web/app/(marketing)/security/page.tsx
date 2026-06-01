import type { Metadata } from "next";
import Section from "@/components/marketing/Section";

export const metadata: Metadata = {
  title: "Security, Laytimely",
  description:
    "How Laytimely handles identity, data at rest, data in transit, access control, audit logging, and incident response.",
};

export default function SecurityPage() {
  return (
    <main className="pt-24">
      <Section>
        <p className="text-eyebrow text-secondary">Security</p>
        <h1 className="text-display mt-6 max-w-3xl text-primary">
          How we protect the documents you trust us with.
        </h1>

        <div className="mt-16 grid grid-cols-1 gap-12 md:grid-cols-[1fr_2.2fr]">
          <p className="text-eyebrow text-secondary">Identity</p>
          <p className="text-body-lg text-secondary">
            Sign-in is brokered through AWS Cognito with email-and-password
            credentials, optional MFA, and the option to bring your own SSO
            provider on the Enterprise tier. Session tokens are HMAC-signed,
            HttpOnly cookies with an 8-hour TTL. The product backend verifies
            every request against the Cognito JWKS; there is no shared session
            store to compromise.
          </p>

          <p className="text-eyebrow text-secondary">Data at rest</p>
          <p className="text-body-lg text-secondary">
            Voyage documents land in S3 with SSE-S3 encryption (SSE-KMS with a
            customer-managed key on request). Structured data sits in Aurora
            Serverless v2 Postgres with at-rest encryption enabled. Backups run
            daily and are retained for thirty days.
          </p>

          <p className="text-eyebrow text-secondary">Data in transit</p>
          <p className="text-body-lg text-secondary">
            Every connection terminates at AWS-managed TLS 1.2 or higher.
            Outbound calls to the Claude API and to optional research providers
            use the same TLS posture.
          </p>

          <p className="text-eyebrow text-secondary">Access control</p>
          <p className="text-body-lg text-secondary">
            Every voyage carries the Cognito user identifier of the owner. The
            backend filters every list and detail endpoint against the
            requesting principal. Admin access is short-lived and audited.
          </p>

          <p className="text-eyebrow text-secondary">Audit logging</p>
          <p className="text-body-lg text-secondary">
            Application logs are structured JSON. Authentication events,
            voyage creations, voyage deletions, and revise applies are emitted
            with the actor and a redacted payload. Logs ship to CloudWatch and
            are retained for ninety days.
          </p>

          <p className="text-eyebrow text-secondary">Incident response</p>
          <p className="text-body-lg text-secondary">
            Suspected vulnerabilities and incident reports go to
            <a
              href="mailto:security@laytimely.com"
              className="ml-1 underline underline-offset-4"
            >
              security@laytimely.com
            </a>
            . We acknowledge within one business day and disclose any incident
            that affects customer data to the affected customer within
            seventy-two hours.
          </p>
        </div>
      </Section>
    </main>
  );
}
