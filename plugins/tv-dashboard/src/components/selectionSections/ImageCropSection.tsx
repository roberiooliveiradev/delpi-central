import { ComunicadoImageCropPanel } from "../deck/ComunicadoImageCropPanel";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import type { SelectionSectionLayout } from "./types";

/** Recorte de imagem — painel (já traz DeckPropertySection). */
export function ImageCropSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (!selected || selected.type !== "image") return null;
  return (
    <div id="td-comunicado-crop-panel">
      <ComunicadoImageCropPanel />
    </div>
  );
}
