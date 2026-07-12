import { FieldLabel, HintAction } from "@delpi/plugin-ui/index";
import { ArrowDown, ArrowUp, Copy, Crop, FolderOpen, Trash2, Upload } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TdRibbonSelect } from "../tdRibbonUi";
import { useComunicadoEditor } from "../comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/** Organizar / opacidade — borda/contorno, sombra e raio ficam em Aparência e Posição e tamanho. */
export function FormatRibbonOrganizeSection({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    uploading,
    updateSelectedStyle,
    removeSelected,
    duplicateSelected,
    moveLayer,
    triggerUpload,
    openMediaLibrary,
  } = useComunicadoEditor();

  if (!selected) return null;

  const isMediaBlock = selected.type === "image" || selected.type === "video";
  const isImageBlock = selected.type === "image";

  return (
    <DeckRibbonGroup label="Organizar" hint={H.organize}>
      <div className="td-deck-ribbon__organize">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile icon={Copy} label="Duplicar" hint={H.duplicateBlock} onClick={duplicateSelected} />
          {isImageBlock && selected.url ? (
            <DeckRibbonTile
              icon={Crop}
              label="Recorte"
              hint={H.cropImage}
              onClick={() => {
                document.getElementById("td-comunicado-crop-panel")?.scrollIntoView({
                  behavior: "smooth",
                  block: "nearest",
                });
              }}
            />
          ) : null}
          {isMediaBlock ? (
            <>
              <DeckRibbonTile
                icon={FolderOpen}
                label="Biblioteca"
                hint={H.mediaLibrary}
                onClick={() => openMediaLibrary("block")}
              />
              <DeckRibbonTile
                icon={Upload}
                label={uploading ? "…" : (labels.comunicadoUpload ?? "Mídia")}
                hint={E.uploadMedia}
                disabled={uploading}
                onClick={() => triggerUpload("block")}
              />
            </>
          ) : null}
          <DeckRibbonTile icon={ArrowUp} label="Frente" hint={E.layerUp} onClick={() => moveLayer("up")} />
          <DeckRibbonTile
            icon={ArrowDown}
            label="Fundo"
            hint={E.layerDown}
            onClick={() => moveLayer("down")}
          />
          <DeckRibbonTile icon={Trash2} label="Remover" hint={E.remove} onClick={removeSelected} />
        </div>
        <div className="td-deck-ribbon__organize-props">
          <FieldLabel
            htmlFor="td-block-opacity"
            label="Opacidade"
            hint={H.opacity}
            className="td-deck-ribbon__field-label"
          />
          <HintAction hint={H.opacity} ariaLabel="Ajuda: Opacidade">
            <input
              id="td-block-opacity"
              type="range"
              min={10}
              max={100}
              step={5}
              aria-label="Opacidade"
              value={Math.round((selected.style?.opacity ?? 1) * 100)}
              onChange={(e) => updateSelectedStyle({ opacity: Number(e.target.value) / 100 })}
            />
          </HintAction>
          {isMediaBlock ? (
            <>
              <FieldLabel
                htmlFor="td-block-object-fit"
                label="Ajuste"
                hint={H.objectFit}
                className="td-deck-ribbon__field-label"
              />
              <TdRibbonSelect
                id="td-block-object-fit"
                className="td-deck-ribbon__select td-deck-ribbon__select--compact"
                aria-label="Ajuste"
                value={selected.style?.objectFit ?? "cover"}
                onChange={(value) =>
                  updateSelectedStyle({
                    objectFit: value as "cover" | "contain",
                  })
                }
                options={[
                  { value: "cover", label: "Preencher" },
                  { value: "contain", label: "Conter" },
                ]}
              />
            </>
          ) : null}
        </div>
      </div>
    </DeckRibbonGroup>
  );
}
