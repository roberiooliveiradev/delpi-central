import { InputBindingInspector } from "../InputBindingInspector";
import { InputViewOptionsInspector } from "../InputViewOptionsInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

/**
 * Binding + elementos do filtro (input) — painel.
 * Ribbon: chrome em ShapeRibbon / shapeChrome.
 */
export function InputBindingSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (!selected || selected.type !== "input") return null;
  return (
    <>
      <InputBindingInspector pane />
      <InputViewOptionsInspector pane />
    </>
  );
}
