import { ArrowLeft } from "lucide-react";

import type { SelectionChromeMode } from "../../utils/resolveSelectionChromeMode";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";

type PartChrome = Extract<SelectionChromeMode, { mode: "part" }>;

/** Nav «voltar à seleção do bloco» quando uma parte está ativa. */
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
