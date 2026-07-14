import { FieldLabel } from "@delpi/plugin-ui/index";
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
import { DeckRangeField } from "../deck/DeckRangeField";
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

type SectionProps = {
  labels?: Labels;
  /** Painel: omite caption do ribbon (accordion já titulou). */
  embed?: boolean;
};

/**
 * Compat: Organizar era ações+camadas no mesmo grupo.
 * Preferir `FormatRibbonOrganizeLayers` + `FormatRibbonElementActions`.
 */
export function FormatRibbonOrganizeSection({ labels = {}, embed = false }: SectionProps) {
  return (
    <>
      <FormatRibbonOrganizeLayers embed={embed} />
      <FormatRibbonElementActions labels={labels} embed={embed} />
    </>
  );
}

/** Organizar — ordem de camadas (frente / fundo). */
export function FormatRibbonOrganizeLayers({ embed = false }: Omit<SectionProps, "labels">) {
  const { selected, moveLayer } = useComunicadoEditor();
  if (!selected) return null;

  return (
    <DeckRibbonGroup
      label="Organizar"
      hint={H.organize}
      captionPlacement={embed ? "none" : "below"}
    >
      <div className="td-deck-ribbon__organize">
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile icon={ArrowUp} label="Frente" hint={E.layerUp} onClick={() => moveLayer("up")} />
          <DeckRibbonTile
            icon={ArrowDown}
            label="Fundo"
            hint={E.layerDown}
            onClick={() => moveLayer("down")}
          />
        </div>
      </div>
    </DeckRibbonGroup>
  );
}

/** Ações — duplicar, remoção e atalhos de mídia. */
export function FormatRibbonElementActions({ labels = {}, embed = false }: SectionProps) {
  const {
    selected,
    uploading,
    removeSelected,
    duplicateSelected,
    triggerUpload,
    openMediaLibrary,
  } = useComunicadoEditor();

  if (!selected) return null;

  const isMediaBlock = selected.type === "image" || selected.type === "video";
  const isImageBlock = selected.type === "image";

  return (
    <DeckRibbonGroup
      label="Ações"
      hint={H.actions ?? H.duplicateBlock}
      captionPlacement={embed ? "none" : "below"}
    >
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
          <ShortcutTip shortcutId="delete">
            <span>
              <DeckRibbonTile icon={Trash2} label="Remover" hint={E.remove} onClick={removeSelected} />
            </span>
          </ShortcutTip>
        </div>
      </div>
    </DeckRibbonGroup>
  );
}

/** @deprecated Preferir `FormatRibbonElementActions`. */
export function FormatRibbonOrganizeActions(props: SectionProps) {
  return <FormatRibbonElementActions {...props} />;
}

/**
 * Campos de opacidade (+ ajuste de mídia) — usados dentro do popover Exibição
 * (posição/tamanho/raio) ou sozinhos quando não há geometria editável.
 */
export function FormatRibbonOpacityFields({
  className = "td-deck-ribbon__organize-props",
}: {
  className?: string;
} = {}) {
  const {
    selected,
    selectedKpiPart,
    selectedChartPart,
    updateSelected,
    updateSelectedStyle,
  } = useComunicadoEditor();

  if (!selected) return null;

  const isMediaBlock = selected.type === "image" || selected.type === "video";

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
    <div className={className}>
      <DeckRangeField
        id="td-block-opacity"
        label="Opacidade"
        hint={H.opacity}
        min={0}
        max={100}
        step={5}
        value={opacityPercent}
        displayValue={`${opacityPercent}%`}
        density="full"
        aria-label="Opacidade"
        onChange={(value) => setOpacity(value / 100)}
      />
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
  );
}

/** @deprecated Preferir seção `display` (= FormatRibbonFrameSection / Tamanho e posição). */
export function FormatRibbonOrganizeDisplay({ embed = false }: Omit<SectionProps, "labels">) {
  return (
    <DeckRibbonGroup
      label="Tamanho e posição"
      hint={H.sizePosition ?? H.display}
      captionPlacement={embed ? "none" : "below"}
    >
      <FormatRibbonOpacityFields />
    </DeckRibbonGroup>
  );
}
