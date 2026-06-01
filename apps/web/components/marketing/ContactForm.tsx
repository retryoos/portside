"use client";

import { useState } from "react";

type Status = "idle" | "submitting" | "success" | "error";

// Web3Forms submission endpoint. The access key is public by design (it only
// authorizes delivery to the address registered with Web3Forms), so it is
// safe to ship in the client bundle. Swap the env value when rotating keys.
const ENDPOINT = "https://api.web3forms.com/submit";
const ACCESS_KEY = process.env.NEXT_PUBLIC_WEB3FORMS_KEY ?? "";

export default function ContactForm() {
  const [status, setStatus] = useState<Status>("idle");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("submitting");

    const form = event.currentTarget;
    const data = new FormData(form);

    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        body: data,
      });
      const json = await res.json();
      if (json.success) {
        setStatus("success");
        form.reset();
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <div className="rounded-card border border-border bg-surface p-8">
        <p className="text-h2 text-primary">Thanks, message received.</p>
        <p className="mt-4 text-body text-secondary">
          We have your note and will reply by email shortly. For anything
          urgent, the direct channels below reach us fastest.
        </p>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-card border border-border bg-surface p-8"
    >
      <input type="hidden" name="access_key" value={ACCESS_KEY} />
      <input type="hidden" name="subject" value="New enquiry from laytimely.com" />
      <input type="hidden" name="from_name" value="Laytimely website" />
      {/* Honeypot: bots fill this, humans never see it. */}
      <input
        type="checkbox"
        name="botcheck"
        className="hidden"
        tabIndex={-1}
        autoComplete="off"
      />

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <label className="block">
          <span className="text-body-sm font-medium text-primary">Name</span>
          <input
            type="text"
            name="name"
            required
            autoComplete="name"
            className="mt-2 w-full rounded-card border border-border bg-neutral px-4 py-2.5 text-body text-primary outline-none focus:border-cta"
          />
        </label>
        <label className="block">
          <span className="text-body-sm font-medium text-primary">Email</span>
          <input
            type="email"
            name="email"
            required
            autoComplete="email"
            className="mt-2 w-full rounded-card border border-border bg-neutral px-4 py-2.5 text-body text-primary outline-none focus:border-cta"
          />
        </label>
      </div>

      <label className="mt-5 block">
        <span className="text-body-sm font-medium text-primary">Company</span>
        <input
          type="text"
          name="company"
          autoComplete="organization"
          className="mt-2 w-full rounded-card border border-border bg-neutral px-4 py-2.5 text-body text-primary outline-none focus:border-cta"
        />
      </label>

      <label className="mt-5 block">
        <span className="text-body-sm font-medium text-primary">
          How can we help?
        </span>
        <textarea
          name="message"
          required
          rows={5}
          className="mt-2 w-full rounded-card border border-border bg-neutral px-4 py-2.5 text-body text-primary outline-none focus:border-cta"
        />
      </label>

      {status === "error" && (
        <p className="mt-4 text-body-sm text-secondary">
          Something went wrong sending that. Please email{" "}
          <a className="underline" href="mailto:sales@laytimely.com">
            sales@laytimely.com
          </a>{" "}
          directly.
        </p>
      )}

      <button
        type="submit"
        disabled={status === "submitting"}
        className="btn-lift mt-7 inline-flex rounded-pill bg-cta px-6 py-3 text-body-sm font-semibold text-on-cta hover:bg-cta-hover disabled:opacity-60"
      >
        {status === "submitting" ? "Sending..." : "Send message"}
      </button>
    </form>
  );
}
