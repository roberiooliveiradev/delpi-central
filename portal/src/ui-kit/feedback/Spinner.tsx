// portal/src/ui-kit/feedback/Spinner.tsx

import type { HTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import "./Spinner.css";

export type SpinnerProps = HTMLAttributes<HTMLDivElement> & {
  label?: string;
  size?: number;
};

export function Spinner({
  label,
  size = 18,
  className,
  ...rest
}: SpinnerProps) {
  const classes = ["portal-ui-spinner", className ?? ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classes} role="status" aria-live="polite" {...rest}>
      <span className="portal-ui-spinner__icon" aria-hidden="true">
        <Loader2 size={size} />
      </span>
      {label ? <span className="portal-ui-spinner__label">{label}</span> : null}
      {!label ? <span className="sr-only">Carregando…</span> : null}
    </div>
  );
}
