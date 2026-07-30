import { Redo2, Undo2 } from "lucide-react";
import type { ReactNode } from "react";

import { HintAction } from "../help/HintAction";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type EditorHistoryActionsClassNames = {
  root: string;
  button: string;
};

export function editorHistoryActionsBemClasses(
  prefix = "delpi-ui",
): EditorHistoryActionsClassNames {
  const base = `${prefix}-editor-history`;
  const ui = "delpi-ui-editor-history";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    button: pair(`${base}__btn`, `${ui}__btn`),
  };
}

const DEFAULT_CN = editorHistoryActionsBemClasses();

/** Rótulo de modificador (Ctrl / ⌘) para hints de atalho. */
export function editorModKeyLabel(): string {
  if (typeof navigator === "undefined") return "Ctrl";
  const platform = navigator.platform ?? "";
  const ua = navigator.userAgent ?? "";
  if (/Mac|iPhone|iPad|iPod/i.test(platform) || /Mac OS X/i.test(ua)) return "⌘";
  return "Ctrl";
}

export function appendShortcutHint(base: string, keys: string): string {
  const trimmed = base.trim();
  if (!trimmed) return keys;
  if (trimmed.includes(keys)) return trimmed;
  if (/atalho\s*:/i.test(trimmed)) return trimmed;
  const letter = keys.replace(/^(Ctrl|⌘)\+/i, "").trim();
  if (letter && new RegExp(`(Ctrl|⌘)\\s*\\+\\s*${letter}`, "i").test(trimmed)) {
    return trimmed;
  }
  return `${trimmed} (${keys})`;
}

export type EditorHistoryActionsProps = {
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  undoLabel: string;
  redoLabel: string;
  undoHint: string;
  redoHint: string;
  ariaLabel: string;
  /** Inclui Ctrl/⌘+Z e Ctrl/⌘+Y nos hints quando ainda não citados. */
  showShortcutHints?: boolean;
  iconSize?: number;
  className?: string;
  classNames?: EditorHistoryActionsClassNames;
  /** Conteúdo à esquerda (ex.: Voltar), no mesmo grupo visual. */
  leading?: ReactNode;
};

/**
 * Desfazer / refazer compactos — visual alinhado ao chrome do TV Dashboard.
 */
export function EditorHistoryActions({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  undoLabel,
  redoLabel,
  undoHint,
  redoHint,
  ariaLabel,
  showShortcutHints = true,
  iconSize = 16,
  className,
  classNames = DEFAULT_CN,
  leading,
}: EditorHistoryActionsProps) {
  const mod = editorModKeyLabel();
  const resolvedUndoHint = showShortcutHints
    ? appendShortcutHint(undoHint, `${mod}+Z`)
    : undoHint;
  const resolvedRedoHint = showShortcutHints
    ? appendShortcutHint(redoHint, `${mod}+Y`)
    : redoHint;

  return (
    <div
      className={[classNames.root, className ?? ""].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      {leading}
      <HintAction hint={resolvedUndoHint} ariaLabel={undoLabel}>
        <button
          type="button"
          className={classNames.button}
          disabled={!canUndo}
          onClick={onUndo}
          aria-label={undoLabel}
          aria-keyshortcuts="Control+Z Meta+Z"
        >
          <Undo2 size={iconSize} strokeWidth={2} aria-hidden="true" />
        </button>
      </HintAction>
      <HintAction hint={resolvedRedoHint} ariaLabel={redoLabel}>
        <button
          type="button"
          className={classNames.button}
          disabled={!canRedo}
          onClick={onRedo}
          aria-label={redoLabel}
          aria-keyshortcuts="Control+Y Meta+Y Control+Shift+Z Meta+Shift+Z"
        >
          <Redo2 size={iconSize} strokeWidth={2} aria-hidden="true" />
        </button>
      </HintAction>
    </div>
  );
}
