import type { ReactElement, ReactNode } from "react";
import { KeyTip, type KeyTipPlacement } from "@delpi/plugin-ui/index";

import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";

type Props = {
  /** Id do catálogo (`TV_KEYBOARD_SHORTCUTS`). */
  shortcutId: string;
  children: ReactElement;
  className?: string;
  /** Preferência; a tela pode inverter se não couber. */
  placement?: KeyTipPlacement;
  /** Desloca o balão horizontalmente (px) para evitar sobreposição. */
  offsetX?: number;
};

/**
 * Envolve um controle e, com Alt ativo (toggle), mostra o atalho em balão
 * (`KeyTip` de `@delpi/plugin-ui`).
 */
export function ShortcutTip({
  shortcutId,
  children,
  className,
  placement = "top",
  offsetX = 0,
}: Props): ReactNode {
  const { altTipsActive, getShortcut, formatKeys } = useKeyboardShortcutsTips();
  const entry = getShortcut(shortcutId);

  if (!entry?.showAltTip) {
    return children;
  }

  return (
    <KeyTip
      label={formatKeys(entry.keys)}
      active={Boolean(altTipsActive)}
      className={className}
      placement={placement}
      offsetX={offsetX}
      variant="shortcut"
      portalScopeClassName="dashboard-tv-dashboard"
      data-td-shortcut={shortcutId}
    >
      {children}
    </KeyTip>
  );
}
