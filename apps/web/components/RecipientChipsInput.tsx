"use client";

// Small chips-style multi-email input. Used by the Email-letter modal for
// the to / cc / bcc fields. Commit a chip on Enter, comma, tab, blur, or
// paste of a comma/whitespace-separated list. Backspace on an empty input
// deletes the last chip. Validation mirrors the backend's pragmatic RFC 5322
// subset (apps/api/laytimely_api/email/models.py); rejections render inline
// with the offending text re-entered so the user can edit.

import { useState, type ClipboardEvent, type KeyboardEvent } from "react";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function isEmail(value: string): boolean {
  return EMAIL_RE.test(value);
}

export default function RecipientChipsInput({
  label,
  values,
  onChange,
  required = false,
  placeholder,
  id,
}: {
  label: string;
  values: string[];
  onChange: (next: string[]) => void;
  required?: boolean;
  placeholder?: string;
  id?: string;
}) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  function commit(raw: string): boolean {
    const candidates = splitCandidates(raw);
    if (candidates.length === 0) return true;
    const next = [...values];
    const seen = new Set(values.map((v) => v.toLowerCase()));
    const bad: string[] = [];
    for (const candidate of candidates) {
      if (!isEmail(candidate)) {
        bad.push(candidate);
        continue;
      }
      const key = candidate.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      next.push(candidate);
    }
    if (bad.length > 0) {
      setError(
        bad.length === 1
          ? `Invalid email: ${bad[0]}`
          : `Invalid emails: ${bad.join(", ")}`,
      );
      // Re-seed the input with the offending text so the user can fix it.
      setDraft(bad.join(", "));
      onChange(next);
      return false;
    }
    setError(null);
    onChange(next);
    setDraft("");
    return true;
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === "," || e.key === "Tab") {
      if (draft.trim().length === 0) {
        // Empty draft + Tab: let focus advance naturally.
        if (e.key !== "Tab") e.preventDefault();
        return;
      }
      e.preventDefault();
      commit(draft);
      return;
    }
    if (e.key === "Backspace" && draft.length === 0 && values.length > 0) {
      e.preventDefault();
      onChange(values.slice(0, -1));
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text");
    if (!/[,\s;]/.test(text)) return;
    e.preventDefault();
    commit(text);
  }

  function removeAt(index: number) {
    onChange(values.filter((_, i) => i !== index));
  }

  return (
    <div>
      <label
        htmlFor={id}
        className="text-eyebrow text-secondary"
      >
        {label}
        {required ? " *" : null}
      </label>
      <div
        className={`mt-2 flex min-h-[44px] flex-wrap items-center gap-1.5 rounded-card border bg-surface px-2.5 py-1.5 transition-colors focus-within:border-primary ${
          error ? "border-danger" : "border-border"
        }`}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.tagName === "BUTTON") return;
          const input = document.getElementById(id ?? "") as HTMLInputElement | null;
          input?.focus();
        }}
      >
        {values.map((addr, i) => (
          <span
            key={`${addr}-${i}`}
            className="inline-flex items-center gap-1 rounded-pill border border-border bg-surface-muted px-2.5 py-1 text-body-sm text-primary"
          >
            {addr}
            <button
              type="button"
              aria-label={`Remove ${addr}`}
              onClick={() => removeAt(i)}
              className="-mr-1 flex h-4 w-4 items-center justify-center rounded-full text-secondary hover:bg-border hover:text-primary"
            >
              <svg
                viewBox="0 0 12 12"
                aria-hidden
                className="h-2.5 w-2.5"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <path d="M3 3l6 6m0-6L3 9" />
              </svg>
            </button>
          </span>
        ))}
        <input
          id={id}
          type="email"
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value);
            if (error) setError(null);
          }}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          onBlur={() => {
            if (draft.trim().length > 0) commit(draft);
          }}
          placeholder={values.length === 0 ? placeholder : ""}
          className="min-w-[12ch] flex-1 bg-transparent px-1 py-0.5 text-body text-primary outline-none placeholder:text-secondary"
        />
      </div>
      {error ? (
        <p className="mt-1.5 text-body-sm text-danger" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function splitCandidates(raw: string): string[] {
  return raw
    .split(/[,;\s]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}
