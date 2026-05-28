import type { ReactNode } from "react";

// Small reusable status chip (DESIGN.md badge-success / badge-warning). Pill-ish,
// tracked-caps label. Used by the correspondence timeline and the outcome table.
type Variant = "success" | "warning";

const VARIANT: Record<Variant, string> = {
  success: "bg-success-container text-success",
  warning: "bg-warning-container text-warning",
};

export default function StatusBadge({
  variant = "success",
  children,
}: {
  variant?: Variant;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-label-caps ${VARIANT[variant]}`}
    >
      {children}
    </span>
  );
}
