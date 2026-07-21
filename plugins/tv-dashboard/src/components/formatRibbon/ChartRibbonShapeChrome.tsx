import { Copy } from "lucide-react";
import {
  applyMarkerStyleToAll,
  chartPartVisualPrimitive,
  chartPrimitiveSupportsFill,
  chartPrimitiveSupportsStroke,
  defaultStrokeWidthForPrimitive,
  getChartPartState,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  resolveBlockShapeChromeBoxShadow,
  upsertChartPartState,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";
import {
  DECK_COLOR_ACCENT,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  ShapeStyleMenu,
} from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ShapeCornerRadiusControl } from "../ShapeCornerRadiusControl";
import { DeckRangeField } from "../deck/DeckRangeField";
import { FormatRibbonOpacityFields } from "./FormatRibbonOrganizeSection";
import { ShapeMenuHint } from "./ShapeMenuHint";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

const CHART_TEXT_CHROME_KINDS = new Set([
  "title",
  "legend",
  "axisTitle",
  "dataLabel",
  "dataLabels",
  "dataTable",
]);

function resolveEffectiveChartPart(
  selectedChartPart: ComunicadoChartPartRef | null,
): ComunicadoChartPartRef {
  if (!selectedChartPart) return { kind: "chartArea" };
  const primitive = chartPartVisualPrimitive(selectedChartPart);
  if (primitive) return selectedChartPart;
  if (CHART_TEXT_CHROME_KINDS.has(selectedChartPart.kind)) return selectedChartPart;
  return { kind: "chartArea" };
}

/**
 * Chrome de forma do gráfico na aba Elemento (estilo / preenchimento / contorno / raio).
 * Alvo: parte selecionada com primitivo visual, ou chartArea por padrão.
 */
export function ChartRibbonShapeChrome({
  block,
  embed = false,
}: {
  block: ComunicadoChartViewBlock;
  /** Painel lateral: omite caption da ribbon (accordion já titulou). */
  embed?: boolean;
}) {
  const { selectedChartPart, updateSelected, updateSelectedStyle } = useComunicadoEditor();
  const effectiveChartPart = resolveEffectiveChartPart(selectedChartPart);
  const chartPartPrimitive =
    chartPartVisualPrimitive(effectiveChartPart) ??
    (CHART_TEXT_CHROME_KINDS.has(effectiveChartPart.kind) ? ("area" as const) : ("area" as const));
  const partState = getChartPartState(block.chartParts, effectiveChartPart);
  const showFill = chartPrimitiveSupportsFill(chartPartPrimitive);
  const showStroke = chartPrimitiveSupportsStroke(chartPartPrimitive);
  const areaChrome =
    effectiveChartPart.kind === "chartArea"
      ? resolveChartAreaStyle(block.chartOptions ?? {}, block.chartParts)
      : effectiveChartPart.kind === "plotArea"
        ? {
            ...resolvePlotAreaStyle(block.chartParts),
            borderRadius: partState?.style?.borderRadius ?? 0,
          }
        : null;
  const fillValue = areaChrome?.fill ?? partState?.style?.fill ?? DECK_COLOR_ACCENT;
  const strokeValue = areaChrome?.stroke ?? partState?.style?.stroke ?? DECK_COLOR_ACCENT;
  const strokeWidth =
    areaChrome?.strokeWidth ??
    partState?.style?.strokeWidth ??
    defaultStrokeWidthForPrimitive(chartPartPrimitive);
  const cornerRadius = areaChrome?.borderRadius ?? partState?.style?.borderRadius ?? 0;
  const showCorners =
    effectiveChartPart.kind === "chartArea" || effectiveChartPart.kind === "plotArea";

  const patchPartStyle = (style: Record<string, unknown>) => {
    const nextParts = upsertChartPartState(block.chartParts, effectiveChartPart, {
      style: style as never,
    });
    const nextOptions = mergeComunicadoChartOptions({
      ...block.chartOptions,
      ...partsToChartOptions(nextParts),
    });
    if (effectiveChartPart.kind === "series" && typeof style.stroke === "string") {
      nextOptions.seriesColor = style.stroke;
    }
    if (effectiveChartPart.kind === "chartArea" && typeof style.fill === "string") {
      nextOptions.backgroundColor = style.fill;
    }
    updateSelected({
      chartParts: nextParts,
      chartOptions: nextOptions,
    } as Partial<ComunicadoBlock>);
  };

  return (
    <>
      <DeckRibbonGroup
        label="Forma"
        hint={H.shapeForma}
        captionPlacement={embed ? "none" : "below"}
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
          <ShapeMenuHint hint={H.shapeStyles} ariaLabel="Ajuda: Estilos de forma">
            <ShapeStyleMenu
              triggerLabel="Estilos"
              onSelect={(preset) =>
                patchPartStyle({
                  fill: preset.fill,
                  stroke: preset.stroke,
                  strokeWidth: preset.strokeWidth,
                  ...(showCorners ? { borderRadius: cornerRadius } : {}),
                })
              }
            />
          </ShapeMenuHint>
          {showCorners ? (
            <ShapeMenuHint hint={H.boxShadow} ariaLabel="Ajuda: Sombra">
              <ShapeShadowMenu
                value={resolveBlockShapeChromeBoxShadow(block)}
                presets={SHADOW_MENU_PRESETS}
                shadowLabel="Sombra"
                onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
              />
            </ShapeMenuHint>
          ) : null}
          {showFill ? (
            <ShapeMenuHint hint={H.shapeFill} ariaLabel="Ajuda: Preenchimento">
              <ShapeFillMenu
                value={fillValue}
                fillLabel={chartPartPrimitive === "point" ? "Cor" : "Preench."}
                onChange={(color) => patchPartStyle({ fill: color })}
                onNoFill={() => patchPartStyle({ fill: "transparent" })}
              />
            </ShapeMenuHint>
          ) : null}
          {showStroke ? (
            <ShapeMenuHint hint={H.shapeOutline} ariaLabel="Ajuda: Contorno">
              <ShapeOutlineMenu
                color={strokeValue}
                strokeWidth={strokeWidth}
                minWidth={0}
                maxWidth={chartPartPrimitive === "point" ? 8 : 20}
                outlineLabel="Contorno"
                onColorChange={(color) => patchPartStyle({ stroke: color })}
                onNoOutline={() => patchPartStyle({ stroke: "transparent", strokeWidth: 0 })}
                onStrokeWidthChange={(width) => patchPartStyle({ strokeWidth: width })}
              />
            </ShapeMenuHint>
          ) : null}
        </div>
        {!showFill && !showStroke ? (
          <p className="td-subtitle td-deck-ribbon__hint">Sem preenchimento nem contorno neste primitivo.</p>
        ) : null}
        <div className="td-deck-ribbon__organize-props td-forma-opacity">
          {showCorners ? (
            <ShapeCornerRadiusControl
              id="td-chart-area-corner-radius"
              value={cornerRadius}
              onChange={(radius) => patchPartStyle({ borderRadius: radius })}
              embedded
            />
          ) : null}
          <FormatRibbonOpacityFields className="td-forma-opacity__slot" />
        </div>
      </DeckRibbonGroup>

      {effectiveChartPart.kind === "marker" ? (
        <DeckRibbonGroup
          label="Marcador"
          hint={H.markerRadius}
          captionPlacement={embed ? "none" : "below"}
        >
          <div className="td-deck-ribbon__toolbar td-deck-ribbon__toolbar--inline">
            <DeckRangeField
              id="td-chart-marker-radius"
              label="Raio"
              hint={H.markerRadius}
              min={1}
              max={12}
              step={0.5}
              value={partState?.style?.markerRadius ?? 2.5}
              density="full"
              onChange={(value) => patchPartStyle({ markerRadius: value || 2.5 })}
            />
            <DeckRibbonTile
              icon={Copy}
              label="Aplicar a todos"
              hint={H.applyMarkerStyleToAll}
              onClick={() => {
                const nextParts = applyMarkerStyleToAll(
                  block.chartParts,
                  block.resolved?.chart?.points?.length ?? 0,
                  effectiveChartPart.kind === "marker" ? effectiveChartPart.seriesIndex ?? 0 : 0,
                  partState?.style ?? {},
                );
                updateSelected({ chartParts: nextParts } as Partial<ComunicadoBlock>);
              }}
            />
          </div>
        </DeckRibbonGroup>
      ) : null}
    </>
  );
}
