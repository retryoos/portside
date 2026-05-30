import type { ReactNode } from "react";

// Small reusable status chip. Pill with a hairline border + tracked-caps label.
// Used by the correspondence timeline and the outcome table.
type Variant = "success" | "warning";

const VARIANT: Record<Variant, string> = {
  success: "border-success/30 bg-success-container text-success",
  warning: "border-warning/30 bg-warning-container text-warning",
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
      className={`inline-flex items-center rounded-pill border px-3 py-1 text-label-caps ${VARIANT[variant]}`}
    >
      {children}
    </span>
  );
}
