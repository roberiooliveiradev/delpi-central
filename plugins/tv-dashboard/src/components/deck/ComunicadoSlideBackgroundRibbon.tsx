import { FolderOpen, Upload } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckRibbonGroup } from "./DeckRibbonGroup";
import { DeckRibbonTile } from "./DeckRibbonTile";

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
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label={labels.comunicadoBackground ?? "Fundo"} hint={E.backgroundColor}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <HintAction hint={E.backgroundColor} ariaLabel="Ajuda: Cor de fundo">
            <label className="td-ribbon-tile td-ribbon-tile--color" aria-label="Cor sólida">
              <span className="td-ribbon-tile__icon">
                <input
                  type="color"
                  className="td-deck-ribbon__color"
                  value={background?.type === "color" ? background.value : "#0f172a"}
                  onChange={(e) => setBackgroundColor(e.target.value)}
                />
              </span>
              <span className="td-ribbon-tile__label">Cor</span>
            </label>
          </HintAction>
          <label className="td-ribbon-tile td-ribbon-tile--inline" aria-label="Gradiente — cor inicial">
            <span className="td-ribbon-tile__icon">
              <input
                type="color"
                className="td-deck-ribbon__color td-deck-ribbon__color--overlay"
                value={gradientFrom}
                onChange={(e) => setBackgroundGradient(e.target.value, gradientTo)}
              />
            </span>
            <span className="td-ribbon-tile__label">Grad. ini.</span>
          </label>
          <label className="td-ribbon-tile td-ribbon-tile--inline" aria-label="Gradiente — cor final">
            <span className="td-ribbon-tile__icon">
              <input
                type="color"
                className="td-deck-ribbon__color td-deck-ribbon__color--overlay"
                value={gradientTo}
                onChange={(e) => setBackgroundGradient(gradientFrom, e.target.value)}
              />
            </span>
            <span className="td-ribbon-tile__label">Grad. fim</span>
          </label>
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

      <DeckRibbonGroup label="Presets" hint="Gradientes prontos para o fundo do slide.">
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
    </div>
  );
}
