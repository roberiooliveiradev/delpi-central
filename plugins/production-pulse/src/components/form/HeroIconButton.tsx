import type { ReactNode } from "react";

import { PpHintAction, PpIconButton } from "../../app/productionPulseUi";

type PpHeroIconButtonProps = {
  hint: string;
  ariaLabel: string;
  onClick: () => void;
  disabled?: boolean;
  children: ReactNode;
  /** Defaults to brand chrome; use `pp-operator-hero-btn` on operator surfaces. */
  className?: string;
  tone?: "default" | "danger";
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
  const classes = ["pp-hero-icon-btn", className].filter(Boolean).join(" ");
  return (
    <PpHintAction hint={hint} ariaLabel={`Ajuda: ${ariaLabel}`}>
      <PpIconButton
        className={classes}
        aria-label={ariaLabel}
        disabled={disabled}
        tone={tone}
        onClick={onClick}
      >
        {children}
      </PpIconButton>
    </PpHintAction>
  );
}
