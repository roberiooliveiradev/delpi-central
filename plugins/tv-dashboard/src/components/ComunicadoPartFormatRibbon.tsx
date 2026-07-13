import { ArrowLeft } from "lucide-react";
import type { ComunicadoChartViewBlock } from "@delpi/tv-dashboard-presentation";

import type { SelectionChromeMode } from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  FormatRibbonFrameSection,
  FormatRibbonOrganizeSection,
  FormatRibbonTypographySections,
} from "./formatRibbon";
import { ChartRibbonShapeChrome } from "./formatRibbon/ChartRibbonShapeChrome";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";

type PartChrome = Extract<SelectionChromeMode, { mode: "part" }>;

type Props = {
  chrome: PartChrome;
};

/**
 * Ribbon quando uma **parte** (gráfico / KPI / tabela) está selecionada.
 * Oculta controles globais do bloco (layout, tipo, galeria, eixos…).
 */
export function ComunicadoPartFormatRibbon({ chrome }: Props) {
  const {
    selected,
    clearChartPartSelection,
    clearKpiPartSelection,
    clearTablePartSelection,
  } = useComunicadoEditor();

  const onBack = () => {
    if (chrome.source === "chart") clearChartPartSelection();
    else if (chrome.source === "kpi") clearKpiPartSelection();
    else clearTablePartSelection();
  };

  return (
    <div className="td-deck-ribbon__groups td-deck-ribbon__groups--part">
      <PartSelectionNav chrome={chrome} onBack={onBack} />
      <FormatRibbonTypographySections />
      {chrome.source === "chart" && selected?.type === "chart_view" ? (
        <ChartRibbonShapeChrome block={selected as ComunicadoChartViewBlock} />
      ) : null}
      <FormatRibbonFrameSection />
      <FormatRibbonOrganizeSection />
      {chrome.source !== "chart" ? (
        <p className="td-subtitle td-deck-ribbon__hint">
          Preenchimento e tipografia finos também no painel Formatar → Parte: {chrome.partLabel}.
        </p>
      ) : null}
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
