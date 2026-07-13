import type { ReactElement, ReactNode } from "react";

import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";

type Props = {
  /** Id do catálogo (`TV_KEYBOARD_SHORTCUTS`). */
  shortcutId: string;
  children: ReactElement;
  className?: string;
  /** Posição do balão relativa ao controle. */
  placement?: "top" | "bottom";
};

/**
 * Envolve um controle e, com Alt segurado, mostra o atalho em balão (KeyTip).
 */
export function ShortcutTip({
  shortcutId,
  children,
  className,
  placement = "top",
}: Props): ReactNode {
  const { altTipsActive, getShortcut, formatKeys } = useKeyboardShortcutsTips();
  const entry = getShortcut(shortcutId);
  if (!entry?.showAltTip) {
    return children;
  }

  const show = altTipsActive;
  return (
    <span
      className={["td-shortcut-tip", className].filter(Boolean).join(" ")}
      data-td-shortcut={shortcutId}
    >
      {children}
      {show ? (
        <span
          className={[
            "td-shortcut-tip__badge",
            placement === "bottom" ? "td-shortcut-tip__badge--bottom" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          role="tooltip"
        >
          {formatKeys(entry.keys)}
        </span>
      ) : null}
    </span>
  );
}
