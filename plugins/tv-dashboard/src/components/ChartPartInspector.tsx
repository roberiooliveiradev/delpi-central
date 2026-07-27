import { FormSelectControl, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  applyMarkerStyleToAll,
  chartPartAllowsDelete,
  chartPartAllowsFrame,
  chartPartVisualPrimitive,
  chartPrimitiveSupportsFill,
  chartPrimitiveSupportsStroke,
  CHART_LEGEND_POSITION_OPTIONS,
  clampChartPartFrame,
  defaultChartPartFrame,
  deleteChartPart,
  formatDesignPx,
  hostRelativeFrameToPageBottomLeftPx,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  patchHostRelativeFramePageBottomLeftPx,
  resolveChartAreaStyle,
  resolveChartDisplayOptions,
  resolvePlotAreaStyle,
  resolveViewportPixelSize,
  serializeChartPartRef,
  upsertChartPartState,
  type ComunicadoChartOptions,
  type ComunicadoChartPartFrame,
  type ComunicadoChartViewBlock,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { ActiveCompositePartSelect } from "./ActiveCompositePartSelect";
import { PartInspectorToolbar } from "./PartInspectorToolbar";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import {
  patchChartSeriesAppearance,
  resolveChartSeriesAppearanceColor,
  resolveChartSeriesColorIndex,
} from "../utils/chartSeriesAppearance";
import { chartPartSelectionLabel } from "../utils/resolveSelectionChromeMode";

type Props = {
  pane?: boolean;
  block: ComunicadoChartViewBlock;
};

function resolveSeriesPointCount(block: ComunicadoChartViewBlock): number {
  const points = block.resolved?.chart?.points;
  if (Array.isArray(points) && points.length > 0) return points.length;
  const markerKeys = Object.keys(block.chartParts ?? {}).filter((key) => key.startsWith("marker:0:"));
  if (markerKeys.length > 0) {
    return Math.max(...markerKeys.map((key) => Number(key.split(":")[2]) + 1), 0);
  }
  return 8;
}

/**
 * Inspetor da parte selecionada do gráfico (Onda 4G.6 / 4H).
 * Estilo herda semântica point/line — stroke na série, fill no marcador.
 */
export function ChartPartInspector({ pane = false, block }: Props) {
  const {
    selectedChartPart,
    clearChartPartSelection,
    beginEditChartPart,
    updateSelected,
    viewportProfile,
  } = useComunicadoEditor();

  if (!selectedChartPart) return null;

  const slideDesign = resolveViewportPixelSize(viewportProfile);
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });
  const displayOptions = resolveChartDisplayOptions(options, block.resolved);
  const primitive = chartPartVisualPrimitive(selectedChartPart);
  const activeSeriesIndex = resolveChartSeriesColorIndex(selectedChartPart);
  const seriesColor = resolveChartSeriesAppearanceColor(block, activeSeriesIndex);
  const partKey = serializeChartPartRef(selectedChartPart);
  const partState = block.chartParts?.[partKey];
  const seriesPartKey = serializeChartPartRef({ kind: "series", seriesIndex: activeSeriesIndex });
  const canDelete = chartPartAllowsDelete(selectedChartPart);
  const frameable = chartPartAllowsFrame(selectedChartPart);
  const defaults = defaultChartPartFrame(selectedChartPart);
  const partFrame = clampChartPartFrame(partState?.frame ?? defaults);
  const partFrameForPx: ComunicadoFrame = {
    x: partFrame.x,
    y: partFrame.y,
    w: partFrame.w ?? defaults.w ?? 20,
    h: partFrame.h ?? defaults.h ?? 20,
  };
  const partFramePx = hostRelativeFrameToPageBottomLeftPx(
    partFrameForPx,
    block.frame,
    slideDesign,
  );
  const chartAreaStyle = resolveChartAreaStyle(options, block.chartParts);
  const plotAreaStyle = resolvePlotAreaStyle(block.chartParts);

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<typeof block>);
  };

  const patchPart = (patch: {
    content?: string;
    visible?: boolean;
    frame?: ComunicadoChartPartFrame | null;
    style?: {
      fill?: string;
      stroke?: string;
      strokeWidth?: number;
      markerRadius?: number;
      opacity?: number;
      borderRadius?: number;
    };
  }) => {
    const nextParts = upsertChartPartState(block.chartParts, selectedChartPart, patch);
    const nextOptions = mergeComunicadoChartOptions({
      ...block.chartOptions,
      ...partsToChartOptions(nextParts),
    });
    if (selectedChartPart.kind === "title" && patch.content !== undefined) {
      nextOptions.title = patch.content;
      nextOptions.showTitle = true;
    }
    if (selectedChartPart.kind === "legend" && patch.content !== undefined) {
      nextOptions.seriesName = patch.content;
    }
    if (selectedChartPart.kind === "chartArea" && patch.style?.fill) {
      nextOptions.backgroundColor = patch.style.fill;
      nextOptions.theme = "light";
    }
    if (selectedChartPart.kind === "series" && (patch.style?.stroke || patch.style?.strokeWidth != null)) {
      const appearance = patchChartSeriesAppearance(block, selectedChartPart.seriesIndex, {
        color: patch.style?.stroke,
        strokeWidth: patch.style?.strokeWidth,
      });
      updateSelected({
        chartParts: appearance.chartParts ?? nextParts,
        chartOptions: appearance.chartOptions ?? nextOptions,
        ...(appearance.chartProjection ? { chartProjection: appearance.chartProjection } : {}),
      } as Partial<typeof block>);
      return;
    }
    updateSelected({
      chartParts: nextParts,
      chartOptions: nextOptions,
    } as Partial<typeof block>);
  };

  const persistSeriesAppearance = (patch: { color?: string; strokeWidth?: number }) => {
    if (selectedChartPart.kind !== "series" && selectedChartPart.kind !== "marker") return;
    const appearance = patchChartSeriesAppearance(block, activeSeriesIndex, patch);
    updateSelected({
      ...(appearance.chartProjection ? { chartProjection: appearance.chartProjection } : {}),
      ...(appearance.chartParts ? { chartParts: appearance.chartParts } : {}),
      ...(appearance.chartOptions ? { chartOptions: appearance.chartOptions } : {}),
    } as Partial<typeof block>);
  };

  const persistPartFrame = (patch: Partial<ComunicadoChartPartFrame>) => {
    patchPart({
      frame: clampChartPartFrame({
        ...partFrame,
        w: partFrame.w ?? defaults.w,
        h: partFrame.h ?? defaults.h,
        ...patch,
      }),
    });
  };

  const persistPartFramePx = (key: "x" | "y" | "w" | "h", rawPx: number) => {
    const nextPct = patchHostRelativeFramePageBottomLeftPx(
      partFrameForPx,
      block.frame,
      key,
      rawPx,
      slideDesign,
    );
    persistPartFrame(nextPct);
  };

  const hideSelectedPart = () => {
    if (!canDelete) return;
    const result = deleteChartPart(block.chartParts, selectedChartPart, block.chartOptions);
    updateSelected({
      chartParts: result.parts,
      chartOptions: result.options,
    } as Partial<typeof block>);
    clearChartPartSelection();
  };

  const applyStyleToAllMarkers = () => {
    if (selectedChartPart.kind !== "marker") return;
    const style = {
      fill: partState?.style?.fill ?? seriesColor,
      stroke: partState?.style?.stroke,
      strokeWidth: partState?.style?.strokeWidth,
      markerRadius: partState?.style?.markerRadius ?? 2.5,
    };
    const nextParts = applyMarkerStyleToAll(
      block.chartParts,
      resolveSeriesPointCount(block),
      selectedChartPart.seriesIndex,
      style,
    );
    updateSelected({ chartParts: nextParts } as Partial<typeof block>);
  };

  return (
    <DeckPropertySection
      pane={pane}
      title={`Parte: ${chartPartSelectionLabel(selectedChartPart)}`}
      hint="Ajuste estilo e conteúdo desta parte. Del oculta a parte (não remove o gráfico)."
      defaultOpen
    >
      <PartInspectorToolbar
        onBack={clearChartPartSelection}
        backLabel="Voltar aos elementos"
        onEditOnStage={
          selectedChartPart.kind === "title" || selectedChartPart.kind === "axisTitle"
            ? () => beginEditChartPart(block.id, selectedChartPart)
            : undefined
        }
        onHide={canDelete ? hideSelectedPart : undefined}
        hideLabel="Ocultar parte"
        hideDanger
        hint="Del também oculta a parte (não remove o gráfico)."
      />

      <ActiveCompositePartSelect id="td-chart-part-active-element" />

      {frameable ? (
        <>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id="td-chart-part-frame-x" label="Posição X (px)">
              <NativeTextControl
                id="td-chart-part-frame-x"
                type="number"
                min={0}
                max={slideDesign.width}
                step={1}
                value={formatDesignPx(partFramePx.x)}
                onChange={(value) => persistPartFramePx("x", Number(value) || 0)}
              />
            </DeckField>
            <DeckField id="td-chart-part-frame-y" label="Posição Y (px)">
              <NativeTextControl
                id="td-chart-part-frame-y"
                type="number"
                min={0}
                max={slideDesign.height}
                step={1}
                value={formatDesignPx(partFramePx.y)}
                onChange={(value) => persistPartFramePx("y", Number(value) || 0)}
              />
            </DeckField>
          </div>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id="td-chart-part-frame-w" label="Largura (px)">
              <NativeTextControl
                id="td-chart-part-frame-w"
                type="number"
                min={1}
                max={slideDesign.width}
                step={1}
                value={formatDesignPx(partFramePx.w)}
                onChange={(value) => persistPartFramePx("w", Number(value) || 1)}
              />
            </DeckField>
            <DeckField id="td-chart-part-frame-h" label="Altura (px)">
              <NativeTextControl
                id="td-chart-part-frame-h"
                type="number"
                min={1}
                max={slideDesign.height}
                step={1}
                value={formatDesignPx(partFramePx.h)}
                onChange={(value) => persistPartFramePx("h", Number(value) || 1)}
              />
            </DeckField>
          </div>
        </>
      ) : null}

      {selectedChartPart.kind === "chartArea" || selectedChartPart.kind === "plotArea" ? (
        <>
          <DeckField id="td-chart-part-area-fill" label="Preenchimento">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Preenchimento"
              value={
                selectedChartPart.kind === "chartArea" ? chartAreaStyle.fill : plotAreaStyle.fill
              }
              onChange={(color) => patchPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-chart-part-area-stroke" label="Cor da borda">
            <TvRibbonColorPicker
              inline
              variant="outline"
              label="Contorno"
              value={
                selectedChartPart.kind === "chartArea" ? chartAreaStyle.stroke : plotAreaStyle.stroke
              }
              onChange={(color) => patchPart({ style: { stroke: color } })}
            />
          </DeckField>
          <div className="td-part-inspector-toolbar__fields-row">
            <DeckField id="td-chart-part-area-stroke-width" label="Espessura">
              <NativeTextControl
                id="td-chart-part-area-stroke-width"
                type="number"
                min={0}
                max={12}
                step={0.5}
                value={
                  selectedChartPart.kind === "chartArea"
                    ? chartAreaStyle.strokeWidth
                    : plotAreaStyle.strokeWidth
                }
                onChange={(value) => patchPart({ style: { strokeWidth: Number(value) || 0 } })}
              />
            </DeckField>
            <DeckField id="td-chart-part-area-radius" label="Cantos (px)">
              <NativeTextControl
                id="td-chart-part-area-radius"
                type="number"
                min={0}
                max={32}
                step={1}
                value={
                  selectedChartPart.kind === "chartArea"
                    ? chartAreaStyle.borderRadius
                    : plotAreaStyle.borderRadius
                }
                onChange={(value) =>
                  patchPart({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
                }
              />
            </DeckField>
          </div>
        </>
      ) : null}

      {selectedChartPart.kind === "title" ? (
        <DeckField id="td-chart-part-title" label="Texto do título">
          <NativeTextControl
            id="td-chart-part-title"
            value={options.title ?? ""}
            placeholder="Ex.: ROL"
            onChange={(value) => {
              persistOptions({
                ...options,
                title: value,
                showTitle: true,
              });
            }}
          />
        </DeckField>
      ) : null}

      {selectedChartPart.kind === "legend" ? (
        <>
          <DeckField id="td-chart-part-legend-name" label="Nome da série">
            <NativeTextControl
              id="td-chart-part-legend-name"
              value={options.seriesName ?? ""}
              onChange={(value) => persistOptions({ ...options, seriesName: value })}
            />
          </DeckField>
          <DeckField id="td-chart-part-legend-position" label="Posição">
            <FormSelectControl
              id="td-chart-part-legend-position"
              ariaLabel="Posição"
              value={options.legendPosition ?? "bottom"}
              onChange={(value) =>
                persistOptions({
                  ...options,
                  legendPosition: value as ComunicadoChartOptions["legendPosition"],
                  showLegend: true,
                })
              }
              options={CHART_LEGEND_POSITION_OPTIONS.filter((entry) => entry.value !== "hidden").map(
                (entry) => ({ value: entry.value, label: entry.label }),
              )}
            />
          </DeckField>
          <DeckField id="td-chart-part-legend-color" label="Cor da série">
            <TvRibbonColorPicker
              inline
              label="Cor da série"
              value={seriesColor}
              onChange={(color) => {
                const appearance = patchChartSeriesAppearance(block, 0, { color });
                updateSelected({
                  ...(appearance.chartProjection ? { chartProjection: appearance.chartProjection } : {}),
                  ...(appearance.chartParts ? { chartParts: appearance.chartParts } : {}),
                  ...(appearance.chartOptions ? { chartOptions: appearance.chartOptions } : {}),
                } as Partial<typeof block>);
              }}
            />
          </DeckField>
        </>
      ) : null}

      {selectedChartPart.kind === "axisTitle" ? (
        <DeckField
          id={`td-chart-part-axis-title-${selectedChartPart.axis}`}
          label={selectedChartPart.axis === "x" ? "Título eixo X" : "Título eixo Y"}
        >
          <NativeTextControl
            id={`td-chart-part-axis-title-${selectedChartPart.axis}`}
            value={
              selectedChartPart.axis === "x"
                ? (options.xAxisTitle?.trim() || displayOptions.xAxisTitle || "")
                : (options.yAxisTitle?.trim() || displayOptions.yAxisTitle || "")
            }
            placeholder={selectedChartPart.axis === "x" ? "Ex.: Mês" : "Ex.: Valor (R$)"}
            onChange={(value) =>
              persistOptions(
                selectedChartPart.axis === "x"
                  ? { ...options, xAxisTitle: value, showXAxisTitle: true }
                  : { ...options, yAxisTitle: value, showYAxisTitle: true },
              )
            }
          />
        </DeckField>
      ) : null}

      {selectedChartPart.kind === "axis" ? (
        <DeckField
          id={`td-chart-part-axis-labels-${selectedChartPart.axis}`}
          label={selectedChartPart.axis === "x" ? "Rótulos eixo X" : "Rótulos eixo Y"}
        >
          <NativeCheckboxControl
            id={`td-chart-part-axis-labels-${selectedChartPart.axis}`}
            checked={
              selectedChartPart.axis === "x"
                ? options.showXAxisLabels !== false
                : options.showYAxisLabels !== false
            }
            label={selectedChartPart.axis === "x" ? "Períodos e categorias" : "Escala de valores"}
            onChange={(checked) =>
              persistOptions(
                selectedChartPart.axis === "x"
                  ? { ...options, showXAxisLabels: checked, showAxes: true }
                  : { ...options, showYAxisLabels: checked, showAxes: true },
              )
            }
          />
        </DeckField>
      ) : null}

      {selectedChartPart.kind === "grid" ? (
        <>
          <DeckField id="td-chart-part-grid-h" label="Grade horizontal">
            <NativeCheckboxControl
              id="td-chart-part-grid-h"
              checked={options.showGrid !== false}
              label="Linhas horizontais"
              onChange={(checked) => persistOptions({ ...options, showGrid: checked })}
            />
          </DeckField>
          <DeckField id="td-chart-part-grid-v" label="Grade vertical">
            <NativeCheckboxControl
              id="td-chart-part-grid-v"
              checked={Boolean(options.showVerticalGrid)}
              label="Linhas verticais"
              onChange={(checked) => persistOptions({ ...options, showVerticalGrid: checked })}
            />
          </DeckField>
        </>
      ) : null}

      {selectedChartPart.kind === "series" && primitive && chartPrimitiveSupportsStroke(primitive) ? (
        <>
          <DeckField id="td-chart-part-series-stroke" label="Cor do traço (linha)">
            <TvRibbonColorPicker
              inline
              label="Cor do traço"
              value={seriesColor}
              onChange={(color) => persistSeriesAppearance({ color })}
            />
          </DeckField>
          <DeckField id="td-chart-part-series-width" label="Espessura">
            <NativeTextControl
              id="td-chart-part-series-width"
              type="number"
              min={1}
              max={8}
              step={0.5}
              value={block.chartParts?.[seriesPartKey]?.style?.strokeWidth ?? 2}
              onChange={(value) =>
                persistSeriesAppearance({ strokeWidth: Number(value) || 2 })
              }
            />
          </DeckField>
          <DeckField id="td-chart-part-series-dash" label="Estilo da linha">
            <FormSelectControl
              id="td-chart-part-series-dash"
              ariaLabel="Estilo da linha"
              value={block.chartParts?.[seriesPartKey]?.style?.strokeDasharray ?? ""}
              onChange={(value) => {
                const nextParts = upsertChartPartState(
                  block.chartParts,
                  { kind: "series", seriesIndex: activeSeriesIndex },
                  {
                    style: {
                      strokeDasharray: value || undefined,
                    },
                  },
                );
                updateSelected({ chartParts: nextParts } as Partial<typeof block>);
              }}
              options={[
                { value: "", label: "Contínua" },
                { value: "6 4", label: "Tracejada" },
                { value: "2 3", label: "Pontilhada" },
                { value: "8 3 2 3", label: "Traço-ponto" },
              ]}
            />
          </DeckField>
          {block.chartProjection?.series?.[activeSeriesIndex] ? (
            <DeckField id="td-chart-part-series-plot" label="Eixo de plotagem">
              <FormSelectControl
                id="td-chart-part-series-plot"
                ariaLabel="Eixo de plotagem"
                value={
                  block.chartProjection.series[activeSeriesIndex]?.plotOn ?? "primary"
                }
                onChange={(value) => {
                  const seriesList = [...(block.chartProjection?.series ?? [])];
                  const current = seriesList[activeSeriesIndex];
                  if (!current) return;
                  seriesList[activeSeriesIndex] = {
                    ...current,
                    plotOn: value === "secondary" ? "secondary" : "primary",
                  };
                  updateSelected({
                    chartProjection: {
                      ...block.chartProjection,
                      series: seriesList,
                    },
                  } as Partial<typeof block>);
                }}
                options={[
                  { value: "primary", label: "Eixo primário (esquerda)" },
                  { value: "secondary", label: "Eixo secundário (direita)" },
                ]}
              />
            </DeckField>
          ) : null}
        </>
      ) : null}

      {selectedChartPart.kind === "marker" && primitive && chartPrimitiveSupportsFill(primitive) ? (
        <>
          <DeckField id="td-chart-part-marker-fill" label="Preenchimento (ponto)">
            <TvRibbonColorPicker
              inline
              variant="fill"
              label="Cor do marcador"
              value={block.chartParts?.[partKey]?.style?.fill ?? seriesColor}
              onChange={(color) => patchPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-chart-part-marker-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
              variant="outline"
              label="Contorno do marcador"
              value={block.chartParts?.[partKey]?.style?.stroke ?? ""}
              onChange={(color) => patchPart({ style: { stroke: color, strokeWidth: 1 } })}
            />
          </DeckField>
          <DeckField id="td-chart-part-marker-radius" label="Tamanho (raio)">
            <NativeTextControl
              id="td-chart-part-marker-radius"
              type="number"
              min={1}
              max={12}
              step={0.5}
              value={block.chartParts?.[partKey]?.style?.markerRadius ?? 2.5}
              onChange={(value) => patchPart({ style: { markerRadius: Number(value) || 2.5 } })}
            />
          </DeckField>
          <button type="button" className="td-deck-btn" onClick={applyStyleToAllMarkers}>
            Aplicar a todos os pontos
          </button>
        </>
      ) : null}
    </DeckPropertySection>
  );
}
