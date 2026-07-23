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
 * Faixa Elemento para KPI — tipografia, aparência e rabo comum (paridade com gráfico).
 */
export function ComunicadoKpiRibbon() {
  const { selected, selectedKpiPart } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedKpiPart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return (
      <DeckRibbonGroups className="td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </DeckRibbonGroups>
    );
  }

  if (!selected || selected.type !== "kpi_view") {
    return (
      <DeckRibbonGroups>
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um KPI no palco para editar elementos, tipografia e aparência.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionTypedWithTailHost
        layout="ribbon"
        typed={["typography", "kpiAppearance", "appearance"]}
      />
    </DeckRibbonGroups>
  );
}
