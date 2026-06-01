import type { Metadata } from "next";
import "./globals.css";

// The ActiveWorkspaceProvider used to live here, wrapping every page.
// That meant marketing visits triggered a ``/api/auth/token`` probe + a
// ``/me/workspaces`` fetch they had no business making. The provider now
// lives under ``app/(app)/layout.tsx`` so only authed product routes mount
// it; marketing and login stay server-only.

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://laytimely.com";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Laytimely · Recover the demurrage you're owed",
    template: "%s · Laytimely",
  },
  description:
    "AI workflows for maritime claims. Three voyage documents in. A finished, cited demurrage claim out, in under a minute.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
