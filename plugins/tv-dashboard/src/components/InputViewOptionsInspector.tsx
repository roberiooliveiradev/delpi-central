import {
  INPUT_ELEMENT_CATALOG,
  isInputElementEnabled,
  setInputElementEnabled,
  type ComunicadoInputBlock,
  type InputElementId,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { InputPartInspector } from "./InputPartInspector";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

/** Catálogo de elementos + inspetor de parte do filtro. */
export function InputViewOptionsInspector({ pane = false }: Props) {
  const { selected, selectedInputPart, updateSelected } = useComunicadoEditor();
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
      <ul className="td-deck-inspector__checklist">
        {INPUT_ELEMENT_CATALOG.filter((item) => item.id !== "inputFrame").map((item) => {
          const enabled = isInputElementEnabled(item.id, block.inputParts, { hasIconName });
          return (
            <li key={item.id}>
              <label className="td-deck-inspector__checkbox">
                <input
                  type="checkbox"
                  checked={enabled}
                  disabled={item.id === "inputControl"}
                  onChange={(event) => {
                    updateSelected({
                      inputParts: setInputElementEnabled(
                        item.id as InputElementId,
                        event.target.checked,
                        block.inputParts,
                      ),
                    } as Partial<ComunicadoInputBlock>);
                  }}
                />
                {item.label}
              </label>
            </li>
          );
        })}
      </ul>
    </DeckPropertySection>
  );
}
