import { ArrowLeft } from "lucide-react";

import type { SelectionChromeMode } from "../utils/resolveSelectionChromeMode";
import { SelectionSectionsHost } from "./selectionSections";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

type PartChrome = Extract<SelectionChromeMode, { mode: "part" }>;

type Props = {
  chrome: PartChrome;
};

/**
 * Ribbon quando uma **parte** (gráfico / tabela) está selecionada.
 * Delega ao host (partFormat + tipografia + frame/organize).
 */
export function ComunicadoPartFormatRibbon({ chrome }: Props) {
  void chrome;
  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--part">
      <SelectionSectionsHost layout="ribbon" full />
    </div>
  );
}

export function PartSelectionNav({
  chrome,
  onBack,
}: {
  chrome: PartChrome;
  onBack: () => void;
}) {
  return (
    <DeckRibbonGroup
      label={`Parte · ${chrome.partLabel}`}
      hint={`Controles desta parte do ${chrome.parentLabel.toLowerCase()} — não do bloco inteiro.`}
    >
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        <DeckRibbonTile
          icon={ArrowLeft}
          label={chrome.backLabel}
          hint={`Sai da parte «${chrome.partLabel}» e volta aos controles do ${chrome.parentLabel.toLowerCase()}.`}
          onClick={onBack}
        />
      </div>
      <p className="td-deck-ribbon__part-banner" role="status">
        Editando <strong>{chrome.partLabel}</strong> ({chrome.parentLabel})
      </p>
    </DeckRibbonGroup>
  );
}
