import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
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
      <div className="td-deck-ribbon__groups td-deck-ribbon__groups--part">
        <SelectionSectionsHost layout="ribbon" full />
      </div>
    );
  }

  if (!selected || selected.type !== "table_view") {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma tabela no palco para editar o design.
        </p>
      </div>
    );
  }

  return (
    <div className="td-deck-ribbon__groups">
      <SelectionTypedWithTailHost
        layout="ribbon"
        typed={["tableStyleOptions", "tableStyles", "tableBorders"]}
      />
    </div>
  );
}
