import { FieldLabel, HintAction, NativeRangeControl } from "@delpi/plugin-ui/index";
import {
  getChartPartState,
  getKpiPartState,
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToChartOptions,
  partsToKpiOptions,
  resolveKpiShapeChromePartRef,
  upsertChartPartState,
  upsertKpiPartState,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
  type ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";
import { ArrowDown, ArrowUp, Copy, Crop, FolderOpen, Trash2, Upload } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { TdRibbonSelect } from "../tdRibbonUi";
import { ShortcutTip } from "../ShortcutTip";
import { useComunicadoEditor } from "../comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

function clampOpacity(value: number): number {
  if (!Number.isFinite(value)) return 1;
  return Math.min(1, Math.max(0, value));
}

/** Organizar / opacidade — borda/contorno, sombra e raio ficam em Aparência e Posição e tamanho. */
export function FormatRibbonOrganizeSection({ labels = {} }: { labels?: Labels }) {
  const {
    selected,
    selectedKpiPart,
    selectedChartPart,
    uploading,
    updateSelected,
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

  const kpiChromePart =
    selected.type === "kpi_view" ? resolveKpiShapeChromePartRef(selectedKpiPart) : null;
  const kpiPartOpacity =
    selected.type === "kpi_view" && kpiChromePart
      ? (getKpiPartState((selected as ComunicadoKpiViewBlock).kpiParts, kpiChromePart)?.style
          ?.opacity ?? 1)
      : null;
  const chartPartOpacity =
    selected.type === "chart_view" && selectedChartPart
      ? (getChartPartState((selected as ComunicadoChartViewBlock).chartParts, selectedChartPart)
          ?.style?.opacity ?? 1)
      : null;

  const opacityValue = clampOpacity(
    kpiPartOpacity != null
      ? kpiPartOpacity
      : chartPartOpacity != null
        ? chartPartOpacity
        : (selected.style?.opacity ?? 1),
  );
  const opacityPercent = Math.round(opacityValue * 100);

  const setOpacity = (raw: number) => {
    const opacity = clampOpacity(raw);
    if (selected.type === "kpi_view" && kpiChromePart) {
      const block = selected as ComunicadoKpiViewBlock;
      const nextParts = upsertKpiPartState(block.kpiParts, kpiChromePart, {
        style: { opacity },
      });
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...partsToKpiOptions(nextParts),
      });
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
      return;
    }
    if (selected.type === "chart_view" && selectedChartPart) {
      const block = selected as ComunicadoChartViewBlock;
      const nextParts = upsertChartPartState(block.chartParts, selectedChartPart, {
        style: { opacity },
      });
      updateSelected({
        chartParts: nextParts,
        chartOptions: mergeComunicadoChartOptions({
          ...block.chartOptions,
          ...partsToChartOptions(nextParts),
        }),
      } as Partial<ComunicadoBlock>);
      return;
    }
    updateSelectedStyle({ opacity });
  };

  return (
    <DeckRibbonGroup label="Organizar" hint={H.organize}>
      <div className="td-deck-ribbon__organize">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <ShortcutTip shortcutId="duplicate">
            <span>
              <DeckRibbonTile
                icon={Copy}
                label="Duplicar"
                hint={H.duplicateBlock}
                onClick={duplicateSelected}
              />
            </span>
          </ShortcutTip>
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
          <ShortcutTip shortcutId="delete">
            <span>
              <DeckRibbonTile icon={Trash2} label="Remover" hint={E.remove} onClick={removeSelected} />
            </span>
          </ShortcutTip>
        </div>
        <div className="td-deck-ribbon__organize-props">
          <FieldLabel
            htmlFor="td-block-opacity"
            label="Opacidade"
            hint={H.opacity}
            className="td-deck-ribbon__field-label"
          />
          <HintAction hint={H.opacity} ariaLabel="Ajuda: Opacidade">
            <NativeRangeControl
              id="td-block-opacity"
              className="td-deck-ribbon__opacity-range"
              min={0}
              max={100}
              step={5}
              aria-label="Opacidade"
              value={opacityPercent}
              style={{ ["--td-range-progress" as string]: `${opacityPercent}%` }}
              onChange={(value) => setOpacity(value / 100)}
            />
          </HintAction>
          <span className="td-deck-ribbon__opacity-value" aria-hidden>
            {opacityPercent}%
          </span>
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
