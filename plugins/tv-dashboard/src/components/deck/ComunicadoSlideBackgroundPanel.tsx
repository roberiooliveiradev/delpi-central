import { Upload, FolderOpen } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "./DeckField";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

type Labels = Record<string, string>;

const GRADIENT_PRESETS: Array<{ label: string; from: string; to: string }> = [
  { label: "Azul profundo", from: "#0f172a", to: "#1e3a5f" },
  { label: "DELPI", from: "#05070a", to: "#0d2840" },
  { label: "Pôr do sol", from: "#1e1b4b", to: "#be123c" },
];

export function ComunicadoSlideBackgroundPanel({ labels = {} }: { labels?: Labels }) {
  const { uploading, background, triggerUpload, openMediaLibrary, setBackgroundColor, setBackgroundGradient } =
    useComunicadoEditor();

  const gradientFrom = background?.type === "gradient" ? background.from : "#0f172a";
  const gradientTo = background?.type === "gradient" ? background.to : "#1e3a5f";

  return (
    <DeckPropertySection title={labels.comunicadoBackground ?? "Fundo do slide"} hint={E.backgroundColor}>
      <DeckField id="td-bg-color" label="Cor sólida" hint={E.backgroundColor}>
        <input
          id="td-bg-color"
          type="color"
          className="td-deck-color-input"
          value={background?.type === "color" ? background.value : "#0f172a"}
          onChange={(e) => setBackgroundColor(e.target.value)}
        />
      </DeckField>

      <DeckField id="td-bg-gradient-from" label="Gradiente — cor inicial">
        <input
          id="td-bg-gradient-from"
          type="color"
          className="td-deck-color-input"
          value={gradientFrom}
          onChange={(e) => setBackgroundGradient(e.target.value, gradientTo)}
        />
      </DeckField>
      <DeckField id="td-bg-gradient-to" label="Gradiente — cor final">
        <input
          id="td-bg-gradient-to"
          type="color"
          className="td-deck-color-input"
          value={gradientTo}
          onChange={(e) => setBackgroundGradient(gradientFrom, e.target.value)}
        />
      </DeckField>
      <div className="td-deck-inspector__actions">
        {GRADIENT_PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => setBackgroundGradient(preset.from, preset.to)}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="td-deck-inspector__actions">
        <HintAction hint={E.uploadBackground} ariaLabel="Ajuda: biblioteca de fundo">
          <button type="button" className="td-btn td-btn--sm" onClick={() => openMediaLibrary("background")}>
            <FolderOpen size={15} aria-hidden="true" />
            Biblioteca
          </button>
        </HintAction>
        <HintAction hint={E.uploadBackground} ariaLabel="Ajuda: imagem de fundo">
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={uploading}
            onClick={() => triggerUpload("background")}
          >
            <Upload size={15} aria-hidden="true" />
            {labels.comunicadoUpload ?? "Enviar imagem de fundo"}
          </button>
        </HintAction>
      </div>
    </DeckPropertySection>
  );
}
