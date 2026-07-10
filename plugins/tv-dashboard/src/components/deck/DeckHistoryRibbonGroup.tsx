import { Redo2, Undo2 } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useDeckEditorHistoryContext } from "../../context/deckEditorHistoryContext";
import { DeckRibbonGroup } from "./DeckRibbonGroup";
import { DeckRibbonTile } from "./DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/** Desfazer/refazer global — visível em todas as faixas do editor da programação. */
export function DeckHistoryRibbonGroup() {
  const history = useDeckEditorHistoryContext();
  if (!history) return null;

  return (
    <DeckRibbonGroup
      label="Histórico"
      hint="Desfazer ou refazer alterações na programação ou no slide (Ctrl+Z / Ctrl+Y)."
    >
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={Undo2}
          label="Desfazer"
          hint={H.undo}
          disabled={!history.canUndo}
          onClick={history.undo}
        />
        <DeckRibbonTile
          icon={Redo2}
          label="Refazer"
          hint={H.redo}
          disabled={!history.canRedo}
          onClick={history.redo}
        />
      </div>
    </DeckRibbonGroup>
  );
}
