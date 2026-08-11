import { FolderOpen, ImageOff, Upload } from "lucide-react";
import { solidFromFill } from "@delpi/plugin-ui/index";

import type { Slide } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useAuthenticatedBlobUrl } from "../../hooks/useAuthenticatedBlobUrl";
import { isCustomMessageSlide } from "../../utils/applySlideBatchPatch";
import {
  TV_ALLOWED_FILL_KINDS,
  backgroundToFill,
  fillToBackground,
} from "../../utils/delpiFillAdapter";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { resolveEditorMediaUrl } from "../slideCardPreview";
import { DeckRibbonGroup } from "./DeckRibbonGroup";
import { DeckRibbonTile } from "./DeckRibbonTile";
import { TvRibbonColorPicker } from "./TvRibbonColorPicker";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;
const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

type Labels = Record<string, string>;

function formatCount(template: string, count: number): string {
  return template.replace("{count}", String(count));
}

/** Controles de fundo compactos na faixa da aba Tela (slide personalizado). */
export function ComunicadoSlideBackgroundRibbon({
  labels = {},
  selectedSlides,
}: {
  labels?: Labels;
  selectedSlides?: Slide[];
}) {
  const {
    uploading,
    background,
    playlistId,
    triggerUpload,
    openMediaLibrary,
    setBackgroundColor,
    setBackground,
  } = useComunicadoEditor();
  const customCount = (selectedSlides ?? []).filter(isCustomMessageSlide).length;
  const many = customCount > 1;
  const fill = backgroundToFill(background);

  const imageApiUrl =
    background?.type === "image"
      ? resolveEditorMediaUrl(playlistId, background.assetId, background.url)
      : undefined;
  const { src: imagePreviewSrc } = useAuthenticatedBlobUrl(imageApiUrl);

  return (
    <DeckRibbonGroup
      groupId="slide-background"
      label={
        many
          ? formatCount(H.backgroundSlides, customCount)
          : (labels.comunicadoBackground ?? "Fundo")
      }
      hint={many ? formatCount(H.backgroundSlidesHint, customCount) : E.backgroundColor}
    >
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
        <TvRibbonColorPicker
          hint={E.backgroundColor}
          label="Cor"
          ariaLabel="Cor de fundo do slide"
          value={solidFromFill(fill)}
          fill={fill}
          onChange={setBackgroundColor}
          onFillChange={(next) => setBackground(fillToBackground(next))}
          allowedFillKinds={TV_ALLOWED_FILL_KINDS}
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
        {background?.type === "image" ? (
          <>
            <button
              type="button"
              className="td-deck-ribbon__preset-swatch td-deck-ribbon__bg-image-swatch"
              title="Imagem de fundo atual — preenche a tela"
              aria-label="Imagem de fundo atual"
              style={
                imagePreviewSrc
                  ? {
                      backgroundImage: `url(${JSON.stringify(imagePreviewSrc)})`,
                      backgroundSize: "cover",
                      backgroundPosition: "center",
                      backgroundRepeat: "no-repeat",
                    }
                  : undefined
              }
              onClick={() => openMediaLibrary("background")}
            />
            <DeckRibbonTile
              icon={ImageOff}
              label="Remover"
              hint={E.clearBackground}
              onClick={() => setBackgroundColor("#ffffff")}
            />
          </>
        ) : null}
      </div>
    </DeckRibbonGroup>
  );
}
