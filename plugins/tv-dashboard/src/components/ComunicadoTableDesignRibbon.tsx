import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ComunicadoPartFormatRibbon } from "./ComunicadoPartFormatRibbon";
import { SelectionSectionsHost } from "./selectionSections";

/**
 * Aba contextual «Design da Tabela» — seções compartilhadas (host).
 */
export function ComunicadoTableDesignRibbon() {
  const { selected, selectedTablePart } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedTablePart,
  });
  if (isPartSelectionChrome(selectionChrome)) {
    return <ComunicadoPartFormatRibbon chrome={selectionChrome} />;
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
      <SelectionSectionsHost
        layout="ribbon"
        only={[
          "tableStyleOptions",
          "tableStyles",
          "tableBorders",
          "frame",
          "organize",
        ]}
      />
    </div>
  );
}
