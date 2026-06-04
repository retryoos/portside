/** @type {import('next').NextConfig} */

// The browser talks to the API directly (NEXT_PUBLIC_API_URL), so the CSP must
// allow that origin in connect-src. Everything else stays locked to 'self'.
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
let apiOrigin = "";
try {
  apiOrigin = new URL(apiUrl).origin;
} catch {
  apiOrigin = "";
}

// Next.js injects inline bootstrap scripts (and inline styles via styled-jsx /
// the framework), so script-src/style-src keep 'unsafe-inline'.
//
// 'unsafe-eval' is required in production too: the client-side PDF export
// (html2pdf.js -> jsPDF) calls the Function() constructor, and html2canvas
// spawns a worker from a blob: URL. Without these, "Download PDF" silently
// throws in prod (it worked in dev only because Fast Refresh already enabled
// unsafe-eval). Tightening to nonces / moving PDF generation server-side is a
// follow-up; for now the demo needs the client export to work.
const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "img-src 'self' data: blob:",
  // Google Fonts: the <link> stylesheet is googleapis.com, the font files are
  // gstatic.com. Without these the Fraunces/Inter/JetBrains faces are blocked.
  "font-src 'self' data: https://fonts.gstatic.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
  // html2canvas (bundled in html2pdf.js) renders via a blob: worker.
  "worker-src 'self' blob:",
  // 'self' + the API origin + Web3Forms (the marketing contact form endpoint)
  // + Google Apps Script (the /survey research form posts there with
  // mode:'no-cors'; the /exec endpoint redirects to script.googleusercontent.com,
  // so both hosts are allowed).
  `connect-src 'self'${apiOrigin ? ` ${apiOrigin}` : ""} https://api.web3forms.com https://script.google.com https://script.googleusercontent.com`,
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: csp },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains",
  },
];

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    // Serve Roman's static research survey (apps/web/public/survey/) at the
    // clean path /survey. The files reference their assets relatively, so they
    // resolve under /survey/ unchanged; only the bare path needs mapping.
    return [{ source: "/survey", destination: "/survey/index.html" }];
  },
};

export default nextConfig;
