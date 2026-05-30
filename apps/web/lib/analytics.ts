// Tiny analytics wrapper. The underlying provider can swap (Vercel Analytics,
// Plausible, PostHog) without touching the components that fire events. Today
// it just queues events on window.dataLayer (a harmless global) so the
// behaviour is observable in DevTools and easy to forward later.
//
// Event taxonomy:
//   hero_book_demo
//   hero_see_product
//   cta_strip_book_demo
//   pricing_select_operator
//   pricing_select_partner
//   pricing_select_enterprise
//
// Anything else is ignored. Add to TRACKED_EVENTS before wiring a new one.

const TRACKED_EVENTS = new Set<string>([
  "hero_book_demo",
  "hero_see_product",
  "cta_strip_book_demo",
  "pricing_select_operator",
  "pricing_select_partner",
  "pricing_select_enterprise",
]);

declare global {
  interface Window {
    dataLayer?: unknown[];
  }
}

export function track(event: string, payload: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  if (!TRACKED_EVENTS.has(event)) {
    if (process.env.NODE_ENV !== "production") {
      console.warn(
        `analytics: ignoring unknown event "${event}". Add it to TRACKED_EVENTS in lib/analytics.ts.`,
      );
    }
    return;
  }
  window.dataLayer = window.dataLayer ?? [];
  window.dataLayer.push({ event, ts: Date.now(), ...payload });
}
