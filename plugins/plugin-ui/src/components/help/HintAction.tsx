import type { ReactElement, ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type HintActionProps = {
  hint: string;
  ariaLabel: string;
  placement?: "top" | "bottom";
  /** Oculta o balão (ex.: popover do controle aberto). */
  suppressed?: boolean;
  children: ReactElement;
};

/** Envolve um botão (ou controle) com balão explicativo sem aninhar botões. */
export function HintAction({
  hint,
  ariaLabel,
  placement = "bottom",
  suppressed = false,
  children,
}: HintActionProps): ReactNode {
  return (
    <HelpTooltip
      content={hint}
      ariaLabel={ariaLabel}
      wrap
      placement={placement}
      suppressed={suppressed}
    >
      {children}
    </HelpTooltip>
  );
}
