import { type ReactNode } from "react";
import {
  chartPartVisualPrimitive,
  getInputPartState,
  getKpiPartState,
  inputPartBoxChromeLabels,
  kpiPartBoxChromeLabels,
  mergeComunicadoKpiOptions,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  resolveInputShapeChromePartRef,
  resolveKpiShapeChromePartRef,
  upsertInputPartState,
  upsertKpiPartState,
  type ComunicadoChartViewBlock,
  type ComunicadoInputBlock,
  type ComunicadoKpiViewBlock,
  type ComunicadoTableViewBlock,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
  DECK_INPUT_DEFAULTS,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleRibbonStrip,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../content/comunicadoVisualPresets";
import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import {
  isPartSelectionChrome,
  resolveSelectionChromeMode,
} from "../utils/resolveSelectionChromeMode";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ChartRibbonShapeChrome } from "./formatRibbon/ChartRibbonShapeChrome";
import { TableRibbonShapeChrome } from "./formatRibbon/TableRibbonShapeChrome";
import { PartSelectionNav } from "./ComunicadoPartFormatRibbon";
import { SelectionSectionsHost } from "./selectionSections";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

/**
 * Faixa contextual «Forma» — tipografia/caixa/forma via host;
 * KPI/input/chart/tabela ainda usam chrome tipado + shell compartilhado.
 */
export function ComunicadoShapeRibbon() {
  const {
    selected,
    selectedIds,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    updateSelected,
    updateSelectedStyle,
    clearKpiPartSelection,
    clearInputPartSelection,
    selectedInputPart,
  } = useComunicadoEditor();

  const selectionChrome = resolveSelectionChromeMode({
    selected,
    selectedChartPart,
    selectedKpiPart,
    selectedTablePart,
    selectedInputPart,
  });
  const partChrome = isPartSelectionChrome(selectionChrome) ? selectionChrome : null;

  const multiSelected = selectedIds.length >= 2;

  const textFormatTarget = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
  });

  const selectedChartVisual =
    selected?.type === "chart_view" && selectedChartPart
      ? chartPartVisualPrimitive(selectedChartPart)
      : null;
  const chartTextChromeKinds = new Set([
    "title",
    "legend",
    "axisTitle",
    "dataLabel",
    "dataLabels",
    "dataTable",
  ]);
  const chartPartHasOwnChrome =
    Boolean(selectedChartVisual) ||
    Boolean(selectedChartPart && chartTextChromeKinds.has(selectedChartPart.kind));
  const chartPartPrimitive =
    selected?.type === "chart_view"
      ? (selectedChartVisual ??
        (selectedChartPart && chartTextChromeKinds.has(selectedChartPart.kind)
          ? ("area" as const)
          : selectedChartPart
            ? null
            : ("area" as const)))
      : null;
  const effectiveChartPart =
    selected?.type === "chart_view"
      ? selectedChartPart && chartPartHasOwnChrome
        ? selectedChartPart
        : { kind: "chartArea" as const }
      : null;

  const isShapeBlock = selected?.type === "shape";
  const isIconBlock = selected?.type === "icon";
  const isTextBox = selected?.type === "heading" || selected?.type === "text";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isCanvasTable = selected?.type === "canvas_table";
  const isDataSourceBlock =
    selected?.type === "data_source" || Boolean(selected?.type.startsWith("data_"));
  const isChartPartPrimitive = Boolean(chartPartPrimitive);
  const isKpiChrome = selected?.type === "kpi_view";
  const isTableChrome = selected?.type === "table_view";
  const isInputChrome = selected?.type === "input";
  const hasCapabilityChrome =
    isShapeBlock ||
    isIconBlock ||
    isChartPartPrimitive ||
    isKpiChrome ||
    isTableChrome ||
    isInputChrome ||
    isTextBox ||
    isMediaBlock ||
    isCanvasTable ||
    isDataSourceBlock ||
    textFormatTarget != null ||
    multiSelected;

  if (!hasCapabilityChrome) {
    return (
      <div className="td-deck-ribbon__groups">
        <p className="td-subtitle td-deck-ribbon__hint">
          Selecione um elemento no palco para formatar texto, preenchimento, contorno e organização.
        </p>
      </div>
    );
  }

  const shell = (chrome: ReactNode, opts?: { organize?: boolean }) => (
    <div className="td-deck-ribbon__groups">
      {partChrome && partChrome.source === "kpi" ? (
        <PartSelectionNav chrome={partChrome} onBack={clearKpiPartSelection} />
      ) : null}
      {partChrome && partChrome.source === "input" ? (
        <PartSelectionNav chrome={partChrome} onBack={clearInputPartSelection} />
      ) : null}
      <SelectionSectionsHost layout="ribbon" only={["typography", "textBox"]} />
      <div className="td-deck-ribbon__group-cluster td-deck-ribbon__group-cluster--chrome-frame-organize">
        {chrome}
        <SelectionSectionsHost
          layout="ribbon"
          only={opts?.organize === false ? ["frame"] : ["frame", "organize"]}
        />
      </div>
    </div>
  );

  if (multiSelected) {
    return (
      <div className="td-deck-ribbon__groups">
        <SelectionSectionsHost layout="ribbon" full />
      </div>
    );
  }

  if (isTextBox || isShapeBlock || isIconBlock || isCanvasTable || isMediaBlock) {
    return (
      <div className="td-deck-ribbon__groups">
        <SelectionSectionsHost layout="ribbon" full />
      </div>
    );
  }

  if (
    isChartPartPrimitive &&
    selected?.type === "chart_view" &&
    effectiveChartPart &&
    chartPartPrimitive
  ) {
    const block = selected as ComunicadoChartViewBlock;
    return shell(<ChartRibbonShapeChrome block={block} />);
  }

  if (isKpiChrome && selected?.type === "kpi_view") {
    const block = selected as ComunicadoKpiViewBlock;
    const chromePart = resolveKpiShapeChromePartRef(selectedKpiPart);
    if (!chromePart) {
      return shell(
        <p className="td-subtitle td-deck-ribbon__hint">
          Seleção global do KPI — posição, tamanho e organizar. Clique no fundo ou numa parte
          para formatar preenchimento e contorno.
        </p>,
      );
    }
    const partState = getKpiPartState(block.kpiParts, chromePart);
    const isCardChrome = chromePart.kind === "card";
    const boxLabels = kpiPartBoxChromeLabels(chromePart.kind);
    const cardState = getKpiPartState(block.kpiParts, { kind: "card" });
    const fillValue = isCardChrome
      ? (cardState?.style?.fill ?? block.kpiOptions?.backgroundColor ?? DECK_COLOR_SURFACE)
      : (partState?.style?.fill ?? "transparent");
    const strokeValue = isCardChrome
      ? (cardState?.style?.stroke ?? DECK_COLOR_BORDER)
      : (partState?.style?.stroke ?? "transparent");
    const strokeWidth = isCardChrome
      ? (cardState?.style?.strokeWidth ?? 1)
      : (partState?.style?.strokeWidth ?? 0);

    const patchChromeStyle = (style: Record<string, unknown>) => {
      const nextParts = upsertKpiPartState(block.kpiParts, chromePart, {
        style: style as never,
      });
      const fromParts = partsToKpiOptions(nextParts);
      const nextOptions = mergeComunicadoKpiOptions({
        ...block.kpiOptions,
        ...fromParts,
        ...(isCardChrome && typeof style.fill === "string"
          ? { backgroundColor: style.fill }
          : {}),
      });
      updateSelected({
        kpiParts: mergeKpiPartsWithOptions(nextParts, nextOptions),
        kpiOptions: nextOptions,
      } as Partial<ComunicadoBlock>);
    };

    return shell(
      <DeckRibbonGroup
        label="Aparência"
        hint={
          isCardChrome
            ? H.shape
            : "Fundo e borda da caixa desta parte — não alteram o fundo do card."
        }
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeStyleRibbonStrip
            maxVisible={5}
            onSelect={(preset) =>
              patchChromeStyle({
                fill: preset.fill,
                stroke: preset.stroke,
                strokeWidth: preset.strokeWidth,
              })
            }
          />
          <ShapeFillMenu
            value={fillValue}
            fillLabel={boxLabels.fillShort}
            onChange={(color) => patchChromeStyle({ fill: color })}
            onNoFill={() => patchChromeStyle({ fill: "transparent" })}
          />
          <ShapeOutlineMenu
            color={strokeValue}
            strokeWidth={strokeWidth}
            minWidth={0}
            maxWidth={20}
            outlineLabel={boxLabels.strokeShort}
            onColorChange={(color) => patchChromeStyle({ stroke: color })}
            onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
            onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
          />
          {isCardChrome ? (
            <ShapeShadowMenu
              value={block.style?.boxShadow}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
            />
          ) : null}
        </div>
      </DeckRibbonGroup>,
    );
  }

  if (isInputChrome && selected?.type === "input") {
    const block = selected as ComunicadoInputBlock;
    const chromePart = resolveInputShapeChromePartRef(selectedInputPart) ?? {
      kind: "frame" as const,
    };
    const partState = getInputPartState(block.inputParts, chromePart);
    const isFrameChrome = chromePart.kind === "frame";
    const boxLabels = inputPartBoxChromeLabels(chromePart.kind);
    const fillValue =
      partState?.style?.fill ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.backgroundColor : "transparent");
    const strokeValue =
      partState?.style?.stroke ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.borderColor : "transparent");
    const strokeWidth =
      partState?.style?.strokeWidth ??
      (isFrameChrome ? DECK_INPUT_DEFAULTS.borderWidth : 0);

    const patchChromeStyle = (style: Record<string, unknown>) => {
      updateSelected({
        inputParts: upsertInputPartState(block.inputParts, chromePart, {
          style: style as never,
        }),
      } as Partial<ComunicadoBlock>);
    };

    const frameShadow =
      getInputPartState(block.inputParts, { kind: "frame" })?.style?.boxShadow ??
      block.style?.boxShadow;

    return shell(
      <DeckRibbonGroup label="Aparência" hint={H.shape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeFillMenu
            value={fillValue}
            fillLabel={boxLabels.fillShort}
            onChange={(color) => patchChromeStyle({ fill: color })}
            onNoFill={() => patchChromeStyle({ fill: "transparent" })}
          />
          <ShapeOutlineMenu
            color={strokeValue}
            strokeWidth={strokeWidth}
            minWidth={0}
            maxWidth={20}
            outlineLabel={boxLabels.strokeShort}
            onColorChange={(color) => patchChromeStyle({ stroke: color })}
            onNoOutline={() => patchChromeStyle({ stroke: "transparent", strokeWidth: 0 })}
            onStrokeWidthChange={(width) => patchChromeStyle({ strokeWidth: width })}
          />
          {isFrameChrome ? (
            <ShapeShadowMenu
              value={typeof frameShadow === "string" ? frameShadow : undefined}
              presets={SHADOW_MENU_PRESETS}
              shadowLabel="Sombra"
              onChange={(boxShadow) => {
                const nextShadow = boxShadow?.trim() ? boxShadow : undefined;
                updateSelected({
                  inputParts: upsertInputPartState(block.inputParts, { kind: "frame" }, {
                    style: { boxShadow: nextShadow },
                  }),
                  style: { ...block.style, boxShadow: nextShadow },
                } as Partial<ComunicadoBlock>);
              }}
            />
          ) : null}
        </div>
      </DeckRibbonGroup>,
    );
  }

  if (isTableChrome && selected?.type === "table_view") {
    return shell(<TableRibbonShapeChrome block={selected as ComunicadoTableViewBlock} />);
  }

  if (isDataSourceBlock && selected) {
    return (
      <div className="td-deck-ribbon__groups">
        <SelectionSectionsHost layout="ribbon" full />
      </div>
    );
  }

  return shell(null);
}
