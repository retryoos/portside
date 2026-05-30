"use client";

// LiquidBackgroundFallback: the orb-based DOM background, used when WebGL is
// unavailable. Renders three softly drifting blurred gradient orbs plus an
// accent-tinted cursor pool. Styling lives in apps/web/app/globals.css under
// the .liquid-bg / .liquid-orb / .liquid-cursor classes (kept here for the
// fallback path even though the WebGL canvas is the primary).
//
// Sits fixed behind every page via the .liquid-bg class, so it covers the
// same viewport area the WebGL canvas would have.

import { useEffect, useRef } from "react";

export default function LiquidBackgroundFallback() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let raf = 0;
    let px = 50;
    let py = 50;

    const onMove = (event: MouseEvent) => {
      px = (event.clientX / window.innerWidth) * 100;
      py = (event.clientY / window.innerHeight) * 100;
      if (!raf) {
        raf = requestAnimationFrame(() => {
          el.style.setProperty("--lx", `${px.toFixed(2)}%`);
          el.style.setProperty("--ly", `${py.toFixed(2)}%`);
          raf = 0;
        });
      }
    };
    const onLeave = () => {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      el.style.setProperty("--lx", "50%");
      el.style.setProperty("--ly", "50%");
    };

    window.addEventListener("mousemove", onMove);
    document.documentElement.addEventListener("mouseleave", onLeave);
    return () => {
      window.removeEventListener("mousemove", onMove);
      document.documentElement.removeEventListener("mouseleave", onLeave);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div ref={ref} aria-hidden className="liquid-bg">
      <div className="liquid-orb liquid-orb--warm liquid-orb--a" />
      <div className="liquid-orb liquid-orb--cool liquid-orb--b" />
      <div className="liquid-orb liquid-orb--warm liquid-orb--c" />
      <div className="liquid-cursor" />
    </div>
  );
}
