import type { MetadataRoute } from "next";

// Sitemap covers the public marketing routes only. App routes (gated behind
// auth) are excluded; the robots policy below also blocks them from crawlers.
const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://papership.ai";

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  const ROUTES = ["", "/security", "/privacy", "/terms", "/contact"];
  return ROUTES.map((path) => ({
    url: `${SITE}${path}`,
    lastModified,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : 0.6,
  }));
}
