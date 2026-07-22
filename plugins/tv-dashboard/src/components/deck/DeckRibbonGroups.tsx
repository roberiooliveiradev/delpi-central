import { RibbonGroupsRow, delpiUiClass } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";

const DECK_GROUPS_CN = {
  root: delpiUiClass("td-deck-ribbon__groups", "delpi-ui-ribbon-groups"),
};

type Props = {
  children: ReactNode;
  className?: string;
  /** Desliga colapso (ex.: painel inspector). */
  overflowEnabled?: boolean;
  gap?: number;
};

/**
 * Faixa de grupos da ribbon com overflow responsivo (plugin-ui).
 * Substitui o antigo `<div className="td-deck-ribbon__groups">`.
 */
export function DeckRibbonGroups({
  children,
  className,
  overflowEnabled = true,
  gap = 8,
}: Props) {
  return (
    <RibbonGroupsRow
      className={className}
      classNames={DECK_GROUPS_CN}
      gap={gap}
      overflowEnabled={overflowEnabled}
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
    >
      {children}
    </RibbonGroupsRow>
  );
}
