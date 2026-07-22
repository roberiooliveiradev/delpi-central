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
 * Aba contextual «Tabela Layout» — dados, truncamento, alinhamento + rabo comum (host).
 */
export function ComunicadoTableLayoutRibbon() {
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
          Selecione uma tabela no palco para editar o layout.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionTypedWithTailHost
        layout="ribbon"
        typed={["tableLayoutData", "tableLayoutSize", "tableLayoutAlign"]}
      />
    </DeckRibbonGroups>
  );
}
