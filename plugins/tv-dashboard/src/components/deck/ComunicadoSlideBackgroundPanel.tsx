import { Upload, FolderOpen, ImageOff } from "lucide-react";
import { HintAction, solidFromFill } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useAuthenticatedBlobUrl } from "../../hooks/useAuthenticatedBlobUrl";
import {
  TV_ALLOWED_FILL_KINDS,
  backgroundToFill,
  fillToBackground,
} from "../../utils/delpiFillAdapter";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { resolveEditorMediaUrl } from "../slideCardPreview";
import { DeckField } from "./DeckField";
import { DeckPropertySection } from "./DeckPropertySection";
import { TvRibbonColorPicker } from "./TvRibbonColorPicker";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

type Labels = Record<string, string>;

export function ComunicadoSlideBackgroundPanel({ labels = {} }: { labels?: Labels }) {
  const {
    uploading,
    background,
    playlistId,
    triggerUpload,
    openMediaLibrary,
    setBackgroundColor,
    setBackground,
  } = useComunicadoEditor();
  const imageApiUrl =
    background?.type === "image"
      ? resolveEditorMediaUrl(playlistId, background.assetId, background.url)
      : undefined;
  const { src: imagePreviewSrc } = useAuthenticatedBlobUrl(imageApiUrl);
  const fill = backgroundToFill(background);

  return (
    <DeckPropertySection title={labels.comunicadoBackground ?? "Fundo do slide"} hint={E.backgroundColor}>
      <DeckField id="td-bg-color" label="Cor" hint={E.backgroundColor}>
        <TvRibbonColorPicker
          label="Cor"
          value={solidFromFill(fill)}
          fill={fill}
          onChange={setBackgroundColor}
          onFillChange={(next) => setBackground(fillToBackground(next))}
          allowedFillKinds={TV_ALLOWED_FILL_KINDS}
        />
      </DeckField>

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
