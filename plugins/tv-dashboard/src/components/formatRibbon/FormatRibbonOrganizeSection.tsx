import { FieldLabel, HintAction, NativeTextControl } from "@delpi/plugin-ui/index";
import { ArrowDown, ArrowUp, Copy, Crop, FolderOpen, Trash2, Upload } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  COMUNICADO_BOX_SHADOW_PRESETS,
  matchBoxShadowPreset,
} from "../../content/comunicadoVisualPresets";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { TdRibbonSelect } from "../tdRibbonUi";
import { useComunicadoEditor } from "../comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/** Organizar / opacidade / borda CSS / raio / sombra — para qualquer bloco selecionado. */
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
          <FieldLabel
            htmlFor="td-block-border-width"
            label="Borda"
            hint={H.borderWidth}
            className="td-deck-ribbon__field-label"
          />
          <NativeTextControl
            id="td-block-border-width"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0}
            max={12}
            value={selected.style?.borderWidth ?? 0}
            onChange={(value) =>
              updateSelectedStyle({
                borderWidth: Number(value) || 0,
                borderColor:
                  selected.style?.borderColor && selected.style.borderColor !== "transparent"
                    ? selected.style.borderColor
                    : "#000000",
              })
            }
          />
          <TvRibbonColorPicker
            label="Borda"
            ariaLabel="Cor da borda"
            hint={H.borderColor}
            inline
            variant="outline"
            value={
              !selected.style?.borderColor || selected.style.borderColor === "transparent"
                ? undefined
                : selected.style.borderColor
            }
            onChange={(color) =>
              updateSelectedStyle({
                borderColor: color,
                borderWidth: Math.max(1, selected.style?.borderWidth ?? 1),
              })
            }
            onNoFill={() =>
              updateSelectedStyle({ borderColor: "transparent", borderWidth: 0 })
            }
          />
          <FieldLabel
            htmlFor="td-block-radius"
            label="Raio"
            hint={H.borderRadius}
            className="td-deck-ribbon__field-label"
          />
          <NativeTextControl
            id="td-block-radius"
            type="number"
            className="td-deck-ribbon__number td-deck-ribbon__number--compact"
            min={0}
            max={64}
            value={selected.style?.borderRadius ?? 0}
            onChange={(value) => updateSelectedStyle({ borderRadius: Number(value) || 0 })}
          />
          <FieldLabel
            htmlFor="td-block-shadow"
            label="Sombra"
            hint={H.boxShadow}
            className="td-deck-ribbon__field-label"
          />
          <TdRibbonSelect
            id="td-block-shadow"
            className="td-deck-ribbon__select td-deck-ribbon__select--compact td-deck-ribbon__select--shadow"
            aria-label="Sombra"
            value={matchBoxShadowPreset(selected.style?.boxShadow)}
            onChange={(value) => {
              const preset = COMUNICADO_BOX_SHADOW_PRESETS.find((item) => item.key === value);
              updateSelectedStyle({ boxShadow: preset?.value });
            }}
            options={COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
              value: preset.key,
              label: preset.label,
            }))}
          />
        </div>
      </div>
    </DeckRibbonGroup>
  );
}
