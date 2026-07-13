import { HintAction } from "@delpi/plugin-ui/index";
import { Redo2, Undo2 } from "lucide-react";

import { getKeyboardShortcut, formatShortcutKeys } from "../../content/keyboardShortcuts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import { ShortcutTip } from "../ShortcutTip";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

function hintWithShortcut(base: string, shortcutId: string): string {
  const entry = getKeyboardShortcut(shortcutId);
  if (!entry) return base;
  const keys = formatShortcutKeys(entry.keys);
  if (base.includes(keys) || base.includes(entry.keys)) return base;
  return `${base} (${keys})`;
}

/** Desfazer/refazer global — ícones compactos na faixa de abas. */
export function DeckHistoryTabActions() {
  const history = useDeckEditorHistoryContext();
  if (!history) return null;

  return (
    <div className="td-deck-chrome__history" role="group" aria-label="Histórico">
      <ShortcutTip shortcutId="undo" placement="bottom" offsetX={-18}>
        <span>
          <HintAction hint={hintWithShortcut(H.undo, "undo")} ariaLabel="Desfazer">
            <button
              type="button"
              className="td-deck-chrome__history-btn"
              disabled={!history.canUndo}
              onClick={history.undo}
              aria-label="Desfazer"
            >
              <Undo2 size={14} aria-hidden="true" />
            </button>
          </HintAction>
        </span>
      </ShortcutTip>
      <ShortcutTip shortcutId="redo" placement="bottom" offsetX={18}>
        <span>
          <HintAction hint={hintWithShortcut(H.redo, "redo")} ariaLabel="Refazer">
            <button
              type="button"
              className="td-deck-chrome__history-btn"
              disabled={!history.canRedo}
              onClick={history.redo}
              aria-label="Refazer"
            >
              <Redo2 size={14} aria-hidden="true" />
            </button>
          </HintAction>
        </span>
      </ShortcutTip>
    </div>
  );
}
