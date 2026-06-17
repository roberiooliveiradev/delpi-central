import { HelpCircle } from "lucide-react";
import { useId, type ReactNode } from "react";
import "./HelpTooltip.css";

type HelpTooltipPlacement = "top" | "right" | "bottom";

type HelpTooltipProps = {
  content: string;
  ariaLabel?: string;
  className?: string;
  wrap?: boolean;
  placement?: HelpTooltipPlacement;
  /** Quando definido, controla visibilidade (ex.: gatilho na borda da sidebar). */
  open?: boolean;
  children?: ReactNode;
};

export function HelpTooltip({
  content,
  ariaLabel = "Saiba mais",
  className,
  wrap = false,
  placement = "top",
  open,
  children,
}: HelpTooltipProps) {
  const tooltipId = useId();
  const isControlled = open !== undefined;
  const rootClass = [
    "portal-help-tooltip",
    wrap ? "portal-help-tooltip--wrap" : "",
    placement !== "top" ? `portal-help-tooltip--${placement}` : "",
    isControlled && open ? "portal-help-tooltip--open" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span
      className={rootClass}
      tabIndex={wrap ? 0 : undefined}
      aria-label={wrap ? ariaLabel : undefined}
      aria-describedby={tooltipId}
    >
      {wrap ? (
        children
      ) : (
        <button
          type="button"
          className="portal-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
          onClick={(event) => event.stopPropagation()}
          onMouseDown={(event) => event.stopPropagation()}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      <span id={tooltipId} role="tooltip" className="portal-help-tooltip__bubble">
        {content}
      </span>
    </span>
  );
}

export function FieldLabel({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="portal-field__label">
      {label}
      {hint ? (
        <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} />
      ) : null}
    </span>
  );
}
