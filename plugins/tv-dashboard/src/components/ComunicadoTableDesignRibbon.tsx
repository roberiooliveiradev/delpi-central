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
 * Aba contextual «Design da Tabela» — tipado + rabo comum (host).
 */
export function ComunicadoTableDesignRibbon() {
  const { selected, selectedTablePart } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedTablePart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return (
      <DeckRibbonGroups className="td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </DeckRibbonGroups>
    );
  }

  if (!selected || selected.type !== "table_view") {
    return (
      <DeckRibbonGroups>
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma tabela no palco para editar o design.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionTypedWithTailHost
        layout="ribbon"
        typed={["tableStyleOptions", "tableStyles", "tableTypography", "tableBorders"]}
      />
    </DeckRibbonGroups>
  );
}
