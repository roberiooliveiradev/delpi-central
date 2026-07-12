import {
  COMUNICADO_IMAGE_CROP_FULL,
  normalizeComunicadoImageCrop,
  type ComunicadoImageCrop,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "./DeckField";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const CROP_KEYS: Array<{ key: keyof ComunicadoImageCrop; label: string; max: number }> = [
  { key: "x", label: "Recorte X %", max: 95 },
  { key: "y", label: "Recorte Y %", max: 95 },
  { key: "w", label: "Largura visível %", max: 100 },
  { key: "h", label: "Altura visível %", max: 100 },
];

export function ComunicadoImageCropPanel() {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "image" || !selected.url) return null;

  const crop = selected.imageCrop ?? COMUNICADO_IMAGE_CROP_FULL;

  function setCrop(next: ComunicadoImageCrop) {
    updateSelected({
      imageCrop: normalizeComunicadoImageCrop(next),
    } as Partial<ComunicadoBlock>);
  }

  function updateCropKey(key: keyof ComunicadoImageCrop, value: number) {
    setCrop({ ...crop, [key]: value });
  }

  return (
    <DeckPropertySection title="Recorte da imagem" hint={E.uploadMedia}>
      <div className="td-deck-frame-grid">
        {CROP_KEYS.map(({ key, label, max }) => (
          <DeckField key={key} id={`td-crop-${key}`} label={label} className="td-field--compact">
            <input
              id={`td-crop-${key}`}
              type="range"
              min={0}
              max={max}
              step={1}
              value={Math.round(crop[key])}
              onChange={(event) => updateCropKey(key, Number(event.target.value))}
            />
            <span className="td-deck-inspector__range-value">{Math.round(crop[key])}%</span>
          </DeckField>
        ))}
      </div>
      <button
        type="button"
        className="td-btn td-btn--sm"
        onClick={() => updateSelected({ imageCrop: undefined } as Partial<ComunicadoBlock>)}
      >
        Resetar recorte
      </button>
    </DeckPropertySection>
  );
}
