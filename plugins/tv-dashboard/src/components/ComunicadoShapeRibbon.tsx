import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { SelectionSectionsHost } from "./selectionSections";

/**
 * Faixa Elemento genérica — só SelectionSectionsHost.
 * Chart/tabela Design usam ribbons tipadas; partes chart/tabela também via host no ElementRibbon.
 */
export function ComunicadoShapeRibbon() {
  const { selected, selectedIds, selectedKpiPart, selectedChartPart } = useComunicadoEditor();

  const multiSelected = selectedIds.length >= 2;
  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });

  if (!multiSelected && !selected && textFormatTarget == null) {
    return (
      <DeckRibbonGroups>
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um elemento no palco para formatar texto, preenchimento, contorno e organização.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionSectionsHost layout="ribbon" full />
    </DeckRibbonGroups>
  );
}
