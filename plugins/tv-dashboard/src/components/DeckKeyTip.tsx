import type { ReactElement, ReactNode } from "react";
import { KeyTip, type KeyTipPlacement } from "@delpi/plugin-ui/index";

import { useDeckKeyTips } from "../context/DeckKeyTipsProvider";
import {
  normalizeKeyTipLetter,
  type DeckKeyTipScope,
} from "../utils/deckKeyTips";

type Props = {
  /** Tecla exibida e capturada (ex.: "F1", "N", "1"). */
  letter: string;
  scope: DeckKeyTipScope;
  children: ReactElement;
  className?: string;
  placement?: KeyTipPlacement;
};

/**
 * Anota um controle com KeyTip (abas F1… / ações letra) e mostra balão quando o modo
 * correspondente está ativo — visual canônico em `@delpi/plugin-ui` (`KeyTip`).
 */
export function DeckKeyTip({
  letter,
  scope,
  children,
  className,
  placement = "bottom",
}: Props): ReactNode {
  const { showTabTips, showActionTips } = useDeckKeyTips();
  const tip = normalizeKeyTipLetter(letter);
  const active = scope === "tabs" ? showTabTips : showActionTips;
  const variant = tip.startsWith("F") && tip.length > 1 ? "shortcut" : "letter";

  return (
    <KeyTip
      label={tip}
      active={active}
      className={["td-deck-keytip", className].filter(Boolean).join(" ")}
      placement={placement}
      variant={variant}
      portalScopeClassName="dashboard-tv-dashboard"
      data-td-keytip={tip}
      data-td-keytip-scope={scope}
    >
      {children}
    </KeyTip>
  );
}
