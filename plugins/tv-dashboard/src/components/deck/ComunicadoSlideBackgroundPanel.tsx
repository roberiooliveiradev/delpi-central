import { Upload, FolderOpen, ImageOff } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useAuthenticatedBlobUrl } from "../../hooks/useAuthenticatedBlobUrl";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { resolveEditorMediaUrl } from "../slideCardPreview";
import { COMUNICADO_BACKGROUND_GRADIENT_PRESETS } from "./ComunicadoSlideBackgroundRibbon";
import { DeckField } from "./DeckField";
import { DeckPropertySection } from "./DeckPropertySection";
import { TvRibbonColorPicker } from "./TvRibbonColorPicker";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

type Labels = Record<string, string>;

const GRADIENT_PRESETS = COMUNICADO_BACKGROUND_GRADIENT_PRESETS;

export function ComunicadoSlideBackgroundPanel({ labels = {} }: { labels?: Labels }) {
  const {
    uploading,
    background,
    playlistId,
    triggerUpload,
    openMediaLibrary,
    setBackgroundColor,
    setBackgroundGradient,
  } = useComunicadoEditor();
  const imageApiUrl =
    background?.type === "image"
      ? resolveEditorMediaUrl(playlistId, background.assetId, background.url)
      : undefined;
  const { src: imagePreviewSrc } = useAuthenticatedBlobUrl(imageApiUrl);

  const gradientFrom = background?.type === "gradient" ? background.from : "#0f172a";
  const gradientTo = background?.type === "gradient" ? background.to : "#1e3a5f";

  return (
    <DeckPropertySection title={labels.comunicadoBackground ?? "Fundo do slide"} hint={E.backgroundColor}>
      <DeckField id="td-bg-color" label="Cor sólida" hint={E.backgroundColor}>
        <TvRibbonColorPicker
          label="Cor"
          value={background?.type === "color" ? background.value : "#ffffff"}
          onChange={setBackgroundColor}
        />
      </DeckField>

      <DeckField id="td-bg-gradient-from" label="Gradiente — cor inicial">
        <TvRibbonColorPicker
          label="Início"
          value={gradientFrom}
          onChange={(color) => setBackgroundGradient(color, gradientTo)}
        />
      </DeckField>
      <DeckField id="td-bg-gradient-to" label="Gradiente — cor final">
        <TvRibbonColorPicker
          label="Fim"
          value={gradientTo}
          onChange={(color) => setBackgroundGradient(gradientFrom, color)}
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
        {background?.type === "image" ? (
          <HintAction hint={E.clearBackground} ariaLabel="Ajuda: remover fundo">
            <button type="button" className="td-btn td-btn--sm" onClick={() => setBackgroundColor("#ffffff")}>
              <ImageOff size={15} aria-hidden="true" />
              Remover imagem
            </button>
          </HintAction>
        ) : null}
      </div>
      {background?.type === "image" && imagePreviewSrc ? (
        <div
          className="td-deck-ribbon__bg-image-swatch"
          style={{
            width: "100%",
            height: 72,
            borderRadius: 8,
            backgroundImage: `url(${JSON.stringify(imagePreviewSrc)})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
          aria-hidden
        />
      ) : null}
    </DeckPropertySection>
  );
}
