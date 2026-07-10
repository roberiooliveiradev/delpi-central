import { HintAction } from "@delpi/plugin-ui/index";
import { Redo2, Undo2 } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Desfazer/refazer global — ícones compactos na faixa de abas. */
export function DeckHistoryTabActions() {
  const history = useDeckEditorHistoryContext();
  if (!history) return null;

  return (
    <div className="td-deck-chrome__history" role="group" aria-label="Histórico">
      <HintAction hint={H.undo} ariaLabel="Desfazer">
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
      <HintAction hint={H.redo} ariaLabel="Refazer">
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
    </div>
  );
}
