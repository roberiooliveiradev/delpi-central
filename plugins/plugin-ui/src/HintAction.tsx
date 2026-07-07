import type { ReactElement, ReactNode } from "react";

import { HelpTooltip } from "./HelpTooltip";

export type HintActionProps = {
  hint: string;
  ariaLabel: string;
  placement?: "top" | "bottom";
  children: ReactElement;
};

/** Envolve um botão (ou controle) com balão explicativo sem aninhar botões. */
export function HintAction({
  hint,
  ariaLabel,
  placement = "bottom",
  children,
}: HintActionProps): ReactNode {
  return (
    <HelpTooltip content={hint} ariaLabel={ariaLabel} wrap placement={placement}>
      {children}
    </HelpTooltip>
  );
}
