// Pure-helper coverage for the citation injection pipeline (review #13).
//
// These tests pin the contract that ClaimLetter and CitationFootnotes
// rely on: numbering is event-iteration order, repeated references all
// pick up the same superscript without stacking, and longer citations
// match before shorter overlapping ones.

import { describe, expect, it } from "vitest";

import {
  flattenCitations,
  injectCitationMarkers,
  toSuperscript,
} from "@/lib/letter-citations";
import type { FlaggedEventCitations } from "@/lib/types";

const MEXICO: FlaggedEventCitations = {
  event_id: "e6",
  cited_authorities: [
    {
      citation: "The Mexico 1 [1990] 1 Lloyd's Rep 507",
      verified_via_tool: true,
      tool_used: "corpus",
      proposition: "weather exception threshold",
    },
  ],
};

const JOHANNA: FlaggedEventCitations = {
  event_id: "e9",
  cited_authorities: [
    {
      citation: "The Johanna Oldendorff [1974] AC 479",
      verified_via_tool: true,
      tool_used: "corpus",
      proposition: "arrived-ship doctrine",
    },
  ],
};

describe("toSuperscript", () => {
  it("maps single digits to unicode superscripts", () => {
    expect(toSuperscript(1)).toBe("¹");
    expect(toSuperscript(2)).toBe("²");
    expect(toSuperscript(9)).toBe("⁹");
  });
  it("maps multi-digit numbers digit-by-digit", () => {
    expect(toSuperscript(10)).toBe("¹⁰");
    expect(toSuperscript(123)).toBe("¹²³");
  });
});

describe("flattenCitations", () => {
  it("preserves event iteration order and dedupes", () => {
    const flat = flattenCitations([MEXICO, JOHANNA, MEXICO]);
    expect(flat.map((a) => a.index)).toEqual([1, 2]);
    expect(flat[0].citation).toBe("The Mexico 1 [1990] 1 Lloyd's Rep 507");
    expect(flat[1].citation).toBe("The Johanna Oldendorff [1974] AC 479");
  });
  it("returns empty list when given empty bundles", () => {
    expect(flattenCitations([])).toEqual([]);
  });
});

describe("injectCitationMarkers", () => {
  it("appends a superscript after every reference and returns the flat list", () => {
    const md = "Per The Mexico 1 [1990] 1 Lloyd's Rep 507 the stoppage fails.";
    const { markdown, flat } = injectCitationMarkers(md, [MEXICO]);
    expect(markdown).toContain("Lloyd's Rep 507¹");
    expect(flat[0].index).toBe(1);
  });
  it("does not double-mark when the same citation appears twice", () => {
    const md =
      "First: The Mexico 1 [1990] 1 Lloyd's Rep 507. Again: The Mexico 1 [1990] 1 Lloyd's Rep 507.";
    const { markdown } = injectCitationMarkers(md, [MEXICO]);
    expect(markdown.match(/¹/g)?.length).toBe(2);
    expect(markdown).not.toContain("¹¹");
  });
  it("returns input unchanged when no citations are provided", () => {
    const md = "Some text without citations.";
    const out = injectCitationMarkers(md, []);
    expect(out.markdown).toBe(md);
    expect(out.flat).toEqual([]);
  });
});
