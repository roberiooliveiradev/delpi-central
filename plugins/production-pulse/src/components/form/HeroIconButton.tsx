import type { ReactNode } from "react";

import { PpHintAction, PpIconButton } from "../../app/productionPulseUi";

export type PpHeroIconTone = "default" | "warning" | "danger";

type PpHeroIconButtonProps = {
  hint: string;
  ariaLabel: string;
  onClick: () => void;
  disabled?: boolean;
  children: ReactNode;
  /** Defaults to brand chrome; use `pp-operator-hero-btn` on operator surfaces. */
  className?: string;
  /** `warning` = atenção (desativar/arquivar); `danger` = destrutivo (excluir). */
  tone?: PpHeroIconTone;
};

/**
 * Hero / detail action: icon-only + PpHintAction, brand chrome via `pp-hero-brand-btn`.
 */
export function PpHeroIconButton({
  hint,
  ariaLabel,
  onClick,
  disabled,
  children,
  className = "pp-hero-brand-btn",
  tone = "default",
}: PpHeroIconButtonProps) {
  const classes = [
    "pp-hero-icon-btn",
    tone !== "default" ? `pp-hero-icon-btn--${tone}` : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <PpHintAction hint={hint} ariaLabel={`Ajuda: ${ariaLabel}`}>
      <PpIconButton
        className={classes}
        aria-label={ariaLabel}
        disabled={disabled}
        tone={tone === "danger" ? "danger" : "default"}
        onClick={onClick}
      >
        {children}
      </PpIconButton>
    </PpHintAction>
  );
}
