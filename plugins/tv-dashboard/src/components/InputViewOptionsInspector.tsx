import {
  INPUT_ELEMENT_CATALOG,
  inputElementPrimaryPartRef,
  isInputElementEnabled,
  isInputPartRefEqual,
  setInputElementEnabled,
  type ComunicadoInputBlock,
  type InputElementId,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { InspectorElementRow } from "./InspectorElementRow";
import { InputPartInspector } from "./InputPartInspector";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

/** Catálogo de elementos + inspetor de parte do filtro. */
export function InputViewOptionsInspector({ pane = false }: Props) {
  const { selected, selectedInputPart, selectInputPart, updateSelected } = useComunicadoEditor();
  if (selected?.type !== "input") return null;
  const block = selected as ComunicadoInputBlock;

  if (selectedInputPart) {
    return <InputPartInspector pane={pane} block={block} />;
  }

  const hasIconName = Boolean(block.input?.iconName?.trim());

  return (
    <DeckPropertySection
      pane={pane}
      title="Elementos do filtro"
      hint="Ligue ou desligue subpartes. Duplo clique no palco seleciona a parte para estilizar."
      defaultOpen
    >
      <div
        id="td-input-elements"
        className="td-chart-elements"
        role="group"
        aria-label="Elementos do filtro"
      >
        {INPUT_ELEMENT_CATALOG.filter((item) => item.id !== "inputFrame").map((item) => {
          const elementId = item.id as InputElementId;
          const enabled = isInputElementEnabled(elementId, block.inputParts, { hasIconName });
          const primary = inputElementPrimaryPartRef(elementId);
          const focused = primary
            ? isInputPartRefEqual(selectedInputPart, primary)
            : false;
          const controlLocked = elementId === "inputControl";
          return (
            <InspectorElementRow
              key={item.id}
              id={`td-input-element-${item.id}`}
              label={item.label}
              hint={item.description}
              enabled={enabled}
              focused={focused}
              toggleDisabled={controlLocked}
              onToggle={
                controlLocked
                  ? () => undefined
                  : (next) => {
                      updateSelected({
                        inputParts: setInputElementEnabled(elementId, next, block.inputParts),
                      } as Partial<ComunicadoInputBlock>);
                    }
              }
              onSelect={() => {
                if (primary) selectInputPart(block.id, primary);
              }}
            />
          );
        })}
      </div>
    </DeckPropertySection>
  );
}
