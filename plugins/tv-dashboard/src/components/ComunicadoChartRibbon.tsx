import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { SelectionSectionsHost } from "./selectionSections";

/**
 * Faixa Elemento para gráfico — seções no SelectionSectionsHost.
 */
export function ComunicadoChartRibbon() {
  const { selected, selectedChartPart } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return (
      <div className="td-deck-ribbon__groups td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </div>
    );
  }

  if (!selected || selected.type !== "chart_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um gráfico no palco para editar tipo, rótulos, eixos e tipografia.
        </p>
      </div>
    );
  }

  return (
    <div className="td-deck-ribbon__groups">
      <SelectionSectionsHost
        layout="ribbon"
        only={[
          "typography",
          "chartLayout",
          "chartStyles",
          "chartType",
          "chartLabels",
          "chartAxes",
          "frame",
          "organize",
        ]}
      />
    </div>
  );
}
