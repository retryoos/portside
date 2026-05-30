import Image from "next/image";

// The Laytimely horizontal brand lockup: compass mark + Fraunces SemiBold
// wordmark + indigo accent dot. Fraunces is loaded once in app/layout.tsx
// and reused here ONLY for the wordmark. All product UI stays in Inter
// (per DESIGN.md typography).

type Size = "sm" | "lg";

const SIZE: Record<
  Size,
  { mark: number; gap: string; text: string }
> = {
  // TopNav variant.
  sm: { mark: 28, gap: "gap-2", text: "text-[1.1rem]" },
  // Login card variant.
  lg: { mark: 40, gap: "gap-2.5", text: "text-[1.55rem]" },
};

export default function Wordmark({
  size = "sm",
  className = "",
}: {
  size?: Size;
  className?: string;
}) {
  const s = SIZE[size];
  return (
    <span className={`inline-flex items-center ${s.gap} ${className}`}>
      <Image
        src="/laytimely-logo.jpg"
        alt=""
        aria-hidden
        width={s.mark}
        height={s.mark}
        priority
        className="rounded-sm"
        style={{ width: s.mark, height: s.mark }}
      />
      <span
        className={`font-semibold leading-none tracking-[-0.025em] ${s.text}`}
        style={{
          fontFamily: '"Fraunces", Georgia, serif',
          fontVariationSettings: '"opsz" 144',
        }}
      >
        Laytimely
        <span className="text-accent">.</span>
      </span>
    </span>
  );
}
