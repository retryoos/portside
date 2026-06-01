// Renders the contentEditable claim letter (#LETTER_DOM_ID) to a PDF by walking
// the live DOM into text blocks and drawing them with jsPDF's text API.
//
// Why not html2canvas (the html2pdf.js default): it rasterizes the DOM and
// cannot parse Tailwind v4's oklch() colors (including ::marker pseudo-elements
// and alpha modifiers), so the export silently failed in production. Drawing
// text directly sidesteps colour parsing entirely and yields a smaller,
// selectable, on-brand letter. Like the Word export, it reads the LIVE DOM, so
// any in-browser edits flow into the file.
//
// Mapping mirrors letter-to-docx.ts: h1/h2/h3 -> headings, p -> body, li ->
// bulleted line, inline <strong>/<em> -> bold/italic runs.

import { jsPDF } from "jspdf";

type Run = { text: string; bold: boolean; italic: boolean };
type BlockType = "h1" | "h2" | "h3" | "p" | "li";
type Block = { type: BlockType; runs: Run[] };
type Inheritance = { bold: boolean; italic: boolean };

const HEADING_TAGS: Record<string, BlockType> = { H1: "h1", H2: "h2", H3: "h3" };

// Standard-14 fonts are Latin-1 only. Map the citation superscripts the letter
// injects (¹ ² ³ …) to bracketed digits and drop anything else outside Latin-1
// so the text never renders as tofu.
const SUPERSCRIPT: Record<string, string> = {
  "¹": "1",
  "²": "2",
  "³": "3",
  "⁰": "0",
  "⁴": "4",
  "⁵": "5",
  "⁶": "6",
  "⁷": "7",
  "⁸": "8",
  "⁹": "9",
};

function sanitize(text: string): string {
  let out = "";
  for (const ch of text) {
    if (ch in SUPERSCRIPT) out += `[${SUPERSCRIPT[ch]}]`;
    else if (ch.charCodeAt(0) <= 0xff) out += ch;
    else out += " ";
  }
  return out;
}

function styleFor(type: BlockType): {
  size: number;
  gapBefore: number;
  lineH: number;
  bold: boolean;
} {
  switch (type) {
    case "h1":
      return { size: 15, gapBefore: 16, lineH: 20, bold: true };
    case "h2":
    case "h3":
      return { size: 12.5, gapBefore: 13, lineH: 17, bold: true };
    case "li":
      return { size: 10.5, gapBefore: 3, lineH: 15, bold: false };
    default:
      return { size: 10.5, gapBefore: 9, lineH: 15.5, bold: false };
  }
}

export function letterToPdf(root: HTMLElement): jsPDF {
  const blocks: Block[] = [];
  walk(root, blocks, { bold: false, italic: false });

  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const M = 56; // ~0.78in margin
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  let y = M;

  const newPageIfNeeded = (lineH: number) => {
    if (y + lineH > pageH - M) {
      doc.addPage();
      y = M;
    }
  };

  for (const block of blocks) {
    const s = styleFor(block.type);
    y += s.gapBefore;

    const indent = block.type === "li" ? 14 : 0;
    const leftX = M + indent;
    const lineMaxX = pageW - M;

    // Split runs into whitespace-delimited tokens that keep their style, so we
    // can switch font per word and wrap at the right margin.
    const tokens: Run[] = [];
    for (const run of block.runs) {
      const sanitized = sanitize(run.text);
      for (const piece of sanitized.split(/(\s+)/)) {
        if (piece.length === 0) continue;
        tokens.push({ text: piece, bold: run.bold, italic: run.italic });
      }
    }
    if (tokens.length === 0) continue;

    let x = leftX;
    newPageIfNeeded(s.lineH);
    if (block.type === "li") {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(s.size);
      doc.text("•", M + 4, y);
    }

    for (const tok of tokens) {
      const style = fontStyle(tok.bold || s.bold, tok.italic);
      doc.setFont("helvetica", style);
      doc.setFontSize(s.size);
      const w = doc.getTextWidth(tok.text);
      const isSpace = tok.text.trim().length === 0;
      if (!isSpace && x + w > lineMaxX) {
        y += s.lineH;
        x = leftX;
        newPageIfNeeded(s.lineH);
      }
      // Skip leading whitespace at the start of a wrapped line.
      if (!(isSpace && x === leftX)) {
        doc.text(tok.text, x, y);
        x += w;
      }
    }
    y += s.lineH;
  }

  return doc;
}

function walk(node: Node, out: Block[], inherit: Inheritance): void {
  if (!(node instanceof Element)) return;
  const tag = node.tagName;

  if (tag in HEADING_TAGS) {
    out.push({ type: HEADING_TAGS[tag], runs: inlineRuns(node, inherit) });
    return;
  }
  if (tag === "UL" || tag === "OL") {
    for (const li of Array.from(node.children)) {
      if (li.tagName !== "LI") continue;
      out.push({ type: "li", runs: inlineRuns(li, inherit) });
    }
    return;
  }
  if (tag === "P") {
    const runs = inlineRuns(node, inherit);
    if (runs.some((r) => r.text.trim().length > 0)) out.push({ type: "p", runs });
    return;
  }
  // Wrappers (div, article, section, Reveal): recurse so body text is not lost.
  for (const child of Array.from(node.childNodes)) walk(child, out, inherit);
}

function inlineRuns(node: Node, inherit: Inheritance): Run[] {
  const runs: Run[] = [];
  collect(node, runs, inherit);
  return runs;
}

function collect(node: Node, runs: Run[], inherit: Inheritance): void {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = (node.textContent ?? "").replace(/\s+/g, " ");
    if (text) runs.push({ text, bold: inherit.bold, italic: inherit.italic });
    return;
  }
  if (!(node instanceof Element)) return;
  const tag = node.tagName;
  const next: Inheritance = {
    bold: inherit.bold || tag === "STRONG" || tag === "B",
    italic: inherit.italic || tag === "EM" || tag === "I",
  };
  for (const child of Array.from(node.childNodes)) collect(child, runs, next);
}

function fontStyle(bold: boolean, italic: boolean): string {
  if (bold && italic) return "bolditalic";
  if (bold) return "bold";
  if (italic) return "italic";
  return "normal";
}
