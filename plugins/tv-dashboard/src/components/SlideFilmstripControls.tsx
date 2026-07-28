import { FolderPlus, Plus } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DECK_HOME_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { DeckRibbonLargeButton } from "./deck/DeckRibbonLargeButton";

type Props = {
  onAdd: () => void;
  onAddSection?: () => void;
};

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const K = DECK_HOME_ACTION_KEYTIPS;

/** Controles de slides no filmstrip (acima das prévias). */
export function SlideFilmstripControls({ onAdd, onAddSection }: Props) {
  return (
    <div className="td-deck-filmstrip__controls" aria-label="Controles de slides">
      <DeckRibbonLargeButton
        icon={Plus}
        label="Nova tela"
        hint={H.newSlide}
        primary
        keyTip={K.newSlide}
        onClick={onAdd}
      />
      {onAddSection ? (
        <DeckRibbonLargeButton
          icon={FolderPlus}
          label="Nova seção"
          hint="Agrupa slides e aplica duração, transição e master da seção."
          onClick={onAddSection}
        />
      ) : null}
    </div>
  );
}
