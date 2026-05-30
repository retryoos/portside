import type { MetadataRoute } from "next";

// Crawlers may index the marketing site. Everything under /cases, /vessels,
// /revise, /login, and /api is gated, internal, or both, so we explicitly
// disallow them.
const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://laytimely.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/security", "/privacy", "/terms", "/contact"],
        disallow: ["/cases", "/vessels", "/revise", "/login", "/api/"],
      },
    ],
    sitemap: `${SITE}/sitemap.xml`,
    host: SITE,
  };
}
