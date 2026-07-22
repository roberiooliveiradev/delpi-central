import { FolderOpen, Upload } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "./DeckRibbonGroup";
import { DeckRibbonTile } from "./DeckRibbonTile";
import { TvRibbonColorPicker } from "./TvRibbonColorPicker";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;
const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Labels = Record<string, string>;

export const COMUNICADO_BACKGROUND_GRADIENT_PRESETS: Array<{ label: string; from: string; to: string }> = [
  { label: "Azul profundo", from: "#0f172a", to: "#1e3a5f" },
  { label: "DELPI", from: "#05070a", to: "#0d2840" },
  { label: "Pôr do sol", from: "#1e1b4b", to: "#be123c" },
];

/** Controles de fundo compactos na faixa da aba Tela (slide personalizado). */
export function ComunicadoSlideBackgroundRibbon({ labels = {} }: { labels?: Labels }) {
  const { uploading, background, triggerUpload, openMediaLibrary, setBackgroundColor, setBackgroundGradient } =
    useComunicadoEditor();

  const gradientFrom = background?.type === "gradient" ? background.from : "#0f172a";
  const gradientTo = background?.type === "gradient" ? background.to : "#1e3a5f";

  return (
    <>
      <DeckRibbonGroup
        groupId="slide-background"
        label={labels.comunicadoBackground ?? "Fundo"}
        hint={E.backgroundColor}
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
          <TvRibbonColorPicker
            hint={E.backgroundColor}
            label="Cor"
            ariaLabel="Cor sólida de fundo do slide"
            value={background?.type === "color" ? background.value : "#ffffff"}
            onChange={setBackgroundColor}
          />
          <TvRibbonColorPicker
            label="Grad. ini."
            ariaLabel="Gradiente — cor inicial"
            value={gradientFrom}
            onChange={(color) => setBackgroundGradient(color, gradientTo)}
          />
          <TvRibbonColorPicker
            label="Grad. fim"
            ariaLabel="Gradiente — cor final"
            value={gradientTo}
            onChange={(color) => setBackgroundGradient(gradientFrom, color)}
          />
          <DeckRibbonTile
            icon={Upload}
            label={labels.comunicadoUpload ?? "Enviar"}
            hint={E.uploadBackground}
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          />
          <DeckRibbonTile
            icon={FolderOpen}
            label="Biblioteca"
            hint={H.mediaLibrary}
            onClick={() => openMediaLibrary("background")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup
        groupId="slide-presets"
        label="Presets"
        hint="Gradientes prontos para o fundo do slide."
      >
        <div className="td-deck-ribbon__controls td-deck-ribbon__controls--presets">
          {COMUNICADO_BACKGROUND_GRADIENT_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className="td-deck-ribbon__preset-swatch"
              title={preset.label}
              aria-label={preset.label}
              style={{ backgroundImage: `linear-gradient(135deg, ${preset.from}, ${preset.to})` }}
              onClick={() => setBackgroundGradient(preset.from, preset.to)}
            />
          ))}
        </div>
      </DeckRibbonGroup>
    </>
  );
}
