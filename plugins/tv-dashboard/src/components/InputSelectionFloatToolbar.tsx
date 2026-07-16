import {
  INPUT_ELEMENT_CATALOG,
  inputElementPrimaryPartRef,
  isInputElementEnabled,
  setInputElementEnabled,
  type ComunicadoInputBlock,
  type InputElementId,
} from "@delpi/tv-dashboard-presentation";

import { ComplexSelectionFloatToolbar } from "./ComplexSelectionFloatToolbar";
import { FloatChecklist, FloatChecklistItem } from "./FloatChecklist";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Props = {
  block: ComunicadoInputBlock;
};

/**
 * Float do filtro (input) — + elementos, pincel (parte/chrome), funil (binding).
 * Mesmo shell do gráfico/KPI/tabela.
 */
export function InputSelectionFloatToolbar({ block }: Props) {
  const { updateSelected, selectInputPart, setSelectionPanelTab } = useComunicadoEditor();
  const hasIconName = Boolean(block.input?.iconName?.trim());

  const toggleElement = (elementId: InputElementId, enabled: boolean) => {
    if (elementId === "inputControl" && !enabled) {
      selectInputPart(block.id, inputElementPrimaryPartRef(elementId));
      return;
    }
    updateSelected({
      inputParts: setInputElementEnabled(elementId, enabled, block.inputParts),
    } as Partial<ComunicadoInputBlock>);
    if (enabled) selectInputPart(block.id, inputElementPrimaryPartRef(elementId));
  };

  const openBinding = (close: () => void) => {
    setSelectionPanelTab("data");
    requestAnimationFrame(() => {
      document.getElementById("td-input-binding")?.scrollIntoView({ block: "nearest" });
    });
    close();
  };

  const openElementsPane = (close: () => void) => {
    setSelectionPanelTab("element");
    requestAnimationFrame(() => {
      document.getElementById("td-input-elements")?.scrollIntoView({ block: "nearest" });
    });
    close();
  };

  return (
    <ComplexSelectionFloatToolbar
      blockId={block.id}
      frame={block.frame}
      labels={{
        elements: "Elementos do filtro",
        style: "Aparência do filtro",
        data: "Parâmetro do filtro",
      }}
      renderElements={() => (
        <FloatChecklist aria-label="Elementos do filtro">
          {INPUT_ELEMENT_CATALOG.filter((item) => item.id !== "inputFrame").map((item) => {
            const elementId = item.id as InputElementId;
            const enabled = isInputElementEnabled(elementId, block.inputParts, { hasIconName });
            const controlLocked = elementId === "inputControl";
            return (
              <FloatChecklistItem
                key={item.id}
                label={item.label}
                title={item.description}
                active={enabled}
                disabled={controlLocked && enabled}
                onClick={() => {
                  if (controlLocked && enabled) {
                    selectInputPart(block.id, inputElementPrimaryPartRef(elementId));
                    return;
                  }
                  toggleElement(elementId, !enabled);
                }}
              />
            );
          })}
        </FloatChecklist>
      )}
      renderStyle={(close) => (
        <FloatChecklist aria-label="Aparência do filtro">
          <FloatChecklistItem
            label="Moldura…"
            onClick={() => {
              selectInputPart(block.id, { kind: "frame" });
              setSelectionPanelTab("format");
              close();
            }}
          />
          <FloatChecklistItem
            label="Controle…"
            onClick={() => {
              selectInputPart(block.id, { kind: "control" });
              setSelectionPanelTab("format");
              close();
            }}
          />
          <FloatChecklistItem
            label="Mais opções de elementos…"
            onClick={() => openElementsPane(close)}
          />
        </FloatChecklist>
      )}
      renderData={(close) => (
        <>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => openBinding(close)}
          >
            Parâmetro e escopo…
          </button>
          <button
            type="button"
            className="td-deck-ribbon__cascade-item"
            onClick={() => {
              selectInputPart(block.id, { kind: "label" });
              openBinding(close);
            }}
          >
            Rótulo e ícone…
          </button>
        </>
      )}
    />
  );
}
