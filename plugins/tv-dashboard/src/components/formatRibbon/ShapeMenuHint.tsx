import type { ReactElement, ReactNode } from "react";
import { HintAction } from "@delpi/plugin-ui/index";

type ShapeMenuHintProps = {
  hint: string;
  ariaLabel: string;
  children: ReactElement;
};

/** Envelope com balão de ajuda para triggers Shape*Menu (mesmo padrão da Caixa). */
export function ShapeMenuHint({ hint, ariaLabel, children }: ShapeMenuHintProps): ReactNode {
  return (
    <HintAction hint={hint} ariaLabel={ariaLabel}>
      <div className="td-deck-ribbon__shape-menu-hint">{children}</div>
    </HintAction>
  );
}
