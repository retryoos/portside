"use client";

// Excel laytime export button (W1, notes/architecture_weeks_5_to_8.md §1.1).
//
// Unlike the PDF and Word buttons (which render client-side from the live
// letter DOM), the workbook is rendered server-side by the backend so the
// laytime ledger numbers, total quantum, and letter copy come from one
// authoritative pipeline. We just fetch the bytes and trigger the download via
// the native saveBlob helper. The active route requires an authenticated
// voyage; the api.ts helper attaches the bearer token.

import { useState } from "react";
import { downloadLaytimeXlsx } from "@/lib/api";
import { saveBlob } from "@/lib/save-blob";

export default function ExportXlsxButton({
  voyageId,
  vesselName,
}: {
  voyageId: string;
  vesselName?: string | null;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleExport() {
    setFailed(false);
    setBusy(true);
    try {
      const blob = await downloadLaytimeXlsx(voyageId);
      saveBlob(blob, makeFilename(voyageId, vesselName));
    } catch (err) {
      console.error("Excel export failed", err);
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  const label = busy
    ? "Exporting…"
    : failed
      ? "Export failed, retry"
      : "Download Excel";
  return (
    <button
      type="button"
      onClick={handleExport}
      disabled={busy}
      aria-label={label}
      title={label}
      className="flex h-9 w-9 items-center justify-center rounded-full text-primary transition-colors hover:bg-surface-muted disabled:opacity-50"
    >
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
      >
        {/* Document outline + an "X" mark inside, matching the Word icon's
            shape so the three export buttons read as a set. */}
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <path d="m9 13 6 6" />
        <path d="m15 13-6 6" />
      </svg>
    </button>
  );
}

function makeFilename(voyageId: string, vesselName?: string | null): string {
  const vessel =
    vesselName?.trim().replace(/\s+/g, "-").toLowerCase() ?? "voyage";
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return `laytime-${vessel}-${voyageId}-${today}.xlsx`;
}
