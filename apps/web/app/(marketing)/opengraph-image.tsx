import { ImageResponse } from "next/og";

// Generated social-share card for every marketing route (the link preview on
// LinkedIn / Slack / X / iMessage). On-brand deep-ink surface, off-white text,
// "AI" front and centre. Rendered at request time and cached by Vercel.
//
// Uses next/og's built-in font (no network fetch) so it never fails to render.

export const alt = "Laytimely — AI workflows for maritime operations";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#141414",
          padding: "76px 80px",
          color: "#fafafa",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            fontSize: 30,
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            color: "#cfcfcf",
          }}
        >
          Laytimely
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              display: "flex",
              fontSize: 78,
              fontWeight: 700,
              lineHeight: 1.04,
              letterSpacing: "-0.02em",
              maxWidth: 1000,
            }}
          >
            AI workflows for maritime operations.
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 30,
              fontSize: 34,
              lineHeight: 1.25,
              color: "#a8a8ad",
              maxWidth: 940,
            }}
          >
            Starting with the demurrage claims that used to take days.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 26,
            color: "#8a8a90",
          }}
        >
          <div style={{ display: "flex" }}>
            Three documents in. A cited claim out. Under a minute.
          </div>
          <div style={{ display: "flex", color: "#cfcfcf" }}>laytimely.com</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
