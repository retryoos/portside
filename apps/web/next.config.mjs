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

const isProd = process.env.NODE_ENV === "production";

// Next.js injects inline bootstrap scripts (and inline styles via styled-jsx /
// the framework), so script-src/style-src keep 'unsafe-inline'. Dev also needs
// 'unsafe-eval' for React Fast Refresh. Tightening to nonces is a follow-up.
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
  `script-src 'self' 'unsafe-inline'${isProd ? "" : " 'unsafe-eval'"}`,
  // 'self' + the API origin + Web3Forms (the marketing contact form endpoint).
  `connect-src 'self'${apiOrigin ? ` ${apiOrigin}` : ""} https://api.web3forms.com`,
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
};

export default nextConfig;
