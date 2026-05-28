// Minimal module declaration: html2pdf.js ships no types.
declare module "html2pdf.js" {
  interface Html2PdfOptions {
    margin?: number | [number, number] | [number, number, number, number];
    filename?: string;
    image?: { type?: string; quality?: number };
    html2canvas?: Record<string, unknown>;
    jsPDF?: Record<string, unknown>;
    pagebreak?: { mode?: string | string[] };
  }

  interface Html2PdfWorker {
    set(opt: Html2PdfOptions): Html2PdfWorker;
    from(element: Element | string): Html2PdfWorker;
    save(): Promise<void>;
    toPdf(): Html2PdfWorker;
    get(type: string): Promise<unknown>;
    outputPdf(type?: string): Promise<unknown>;
  }

  function html2pdf(): Html2PdfWorker;
  function html2pdf(element: Element | string, opt?: Html2PdfOptions): Html2PdfWorker;

  export default html2pdf;
}
