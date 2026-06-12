import { HelpCircle } from "lucide-react";
import { useId, type ReactNode } from "react";

type HelpTooltipProps = {
  content: string;
  /** Rótulo acessível do gatilho (padrão: «Saiba mais»). */
  ariaLabel?: string;
  className?: string;
  /** Envolve o conteúdo e exibe o balão ao passar o mouse no conjunto. */
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
  const rootClass = ["dm-help-tooltip", wrap ? "dm-help-tooltip--wrap" : "", className]
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
          className="dm-help-tooltip__trigger"
          aria-label={ariaLabel}
          aria-describedby={tooltipId}
        >
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      )}
      <span id={tooltipId} role="tooltip" className="dm-help-tooltip__bubble">
        {content}
      </span>
    </span>
  );
}

export function FieldLabel({ label, hint }: { label: string; hint?: string }) {
  return (
    <span className="dm-field__label">
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </span>
  );
}
