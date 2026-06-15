import { HelpCircle } from "lucide-react";
import { useId, type ReactNode } from "react";

type HelpTooltipProps = {
  content: string;
  ariaLabel?: string;
  className?: string;
  wrap?: boolean;
  children?: ReactNode;
};

export function HelpTooltip({
  content,
  ariaLabel = "Saiba mais",
  className,
  wrap = false,
  children,
}: HelpTooltipProps) {
  const tooltipId = useId();
  const rootClass = ["dp-help-tooltip", wrap ? "dp-help-tooltip--wrap" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <span
      className={rootClass}
      tabIndex={wrap ? 0 : undefined}
      aria-label={wrap ? ariaLabel : undefined}
      aria-describedby={wrap ? tooltipId : undefined}
    >
      {wrap ? (
        children
      ) : (
        <button
          type="button"
          className="dp-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
          onClick={(event) => event.stopPropagation()}
          onMouseDown={(event) => event.stopPropagation()}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      <span id={tooltipId} role="tooltip" className="dp-help-tooltip__bubble">
        {content}
      </span>
    </span>
  );
}

export function FieldLabel({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="dp-field__label">
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
