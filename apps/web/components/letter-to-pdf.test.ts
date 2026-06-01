// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { letterToPdf } from "@/components/letter-to-pdf";

function buildLetter(): HTMLElement {
  const root = document.createElement("article");
  root.innerHTML = `
    <p>To: Charterers</p>
    <div>
      <p><strong>Aegean Tankers S.A.</strong> Akti Miaouli 1, Piraeus 185 35, Greece</p>
      <h1>1. Summary of claim</h1>
      <ul>
        <li>Demurrage due: EUR 84,375.00</li>
        <li>Laytime used: 117 hours</li>
      </ul>
      <p>Per <em>The Mexico 1</em> the stoppage must count.<sup>¹</sup></p>
    </div>`;
  return root;
}

describe("letterToPdf", () => {
  it("produces a valid, non-empty PDF from the live letter DOM", () => {
    const doc = letterToPdf(buildLetter());
    const bytes = new Uint8Array(doc.output("arraybuffer") as ArrayBuffer);
    expect(bytes.byteLength).toBeGreaterThan(800);
    expect(new TextDecoder("latin1").decode(bytes.slice(0, 5))).toBe("%PDF-");
  });

  it("writes the letter text (incl. the quantum) into the content stream", () => {
    const doc = letterToPdf(buildLetter());
    const raw = doc.output("datauristring");
    const pdf = atob(raw.split(",")[1]!);
    // jsPDF does not compress by default, so tokens appear literally.
    expect(pdf).toContain("84,375.00");
    expect(pdf).toContain("Summary");
    // Citation superscript is mapped to a Latin-1-safe bracketed digit.
    expect(pdf).toContain("[1]");
  });

  it("does not throw on an empty node", () => {
    expect(() => letterToPdf(document.createElement("div"))).not.toThrow();
  });
});
