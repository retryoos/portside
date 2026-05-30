"use client";

import { useEffect, useRef, useState } from "react";

// Auto-playing, muted, looped showcase clip. Falls back gracefully to its
// poster image when no source is available, with a play overlay so the
// frame still reads as "a video would play here". Reduced-motion users
// see the poster only.
export default function LoopVideo({
  src,
  webmSrc,
  poster,
  caption,
}: {
  src?: string;
  webmSrc?: string;
  poster: string;
  caption: string;
}) {
  const ref = useRef<HTMLVideoElement | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const onChange = (event: MediaQueryListEvent) =>
      setReducedMotion(event.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const hasSource = Boolean(src || webmSrc);

  return (
    <figure className="flex flex-col gap-4">
      <div className="relative overflow-hidden rounded-card border border-border bg-surface shadow-card">
        {/* Fixed 16:9 frame so the layout is stable even when the asset is missing. */}
        <div className="relative aspect-[16/9] w-full">
          {hasSource && !reducedMotion ? (
            <video
              ref={ref}
              autoPlay
              muted
              loop
              playsInline
              preload="metadata"
              poster={poster}
              className="h-full w-full object-cover"
            >
              {webmSrc && <source src={webmSrc} type="video/webm" />}
              {src && <source src={src} type="video/mp4" />}
            </video>
          ) : (
            // Poster-only fallback. Background-image used so we don't fail the
            // build when the asset is missing; the browser silently 404s and
            // the surrounding card still reads.
            <div
              role="img"
              aria-label={caption}
              className="h-full w-full bg-surface-muted bg-cover bg-center"
              style={{ backgroundImage: `url(${poster})` }}
            />
          )}
        </div>
      </div>
      <figcaption className="text-body-sm text-secondary">{caption}</figcaption>
    </figure>
  );
}
