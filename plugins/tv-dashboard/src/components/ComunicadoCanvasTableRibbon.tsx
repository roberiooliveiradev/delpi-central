import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { SelectionTypedWithTailHost } from "./selectionSections";

/**
 * Faixa Elemento para Grade (`canvas_table`) — estrutura, estilo e tipografia do bloco.
 * Moldura (fill/stroke) fica no rabo comum / Forma via appearance.
 */
export function ComunicadoCanvasTableRibbon() {
  const { selected } = useComunicadoEditor();

  if (!selected || selected.type !== "canvas_table") {
    return (
      <DeckRibbonGroups>
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione uma Grade no palco para editar estrutura, estilo e tipografia.
        </p>
      </DeckRibbonGroups>
    );
  }

  return (
    <DeckRibbonGroups>
      <SelectionTypedWithTailHost layout="ribbon" typed={["canvasTable", "appearance"]} />
    </DeckRibbonGroups>
  );
}
