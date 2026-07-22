import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import {
  SelectionSectionsHost,
  SelectionTypedWithTailHost,
} from "./selectionSections";

/**
 * Faixa Elemento para gráfico — seções tipadas + rabo comum no host.
 */
export function ComunicadoChartRibbon() {
  const { selected, selectedChartPart } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return (
      <DeckRibbonGroups className="td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </DeckRibbonGroups>
    );
  }

  if (!selected || selected.type !== "chart_view") {
    return (
      <DeckRibbonGroups>
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um gráfico no palco para editar tipo, rótulos, eixos e tipografia.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionTypedWithTailHost
        layout="ribbon"
        typed={[
          "typography",
          "chartLayout",
          "chartStyles",
          "chartType",
          "chartLabels",
          "chartAxes",
          "chartSeries",
        ]}
      />
    </DeckRibbonGroups>
  );
}
