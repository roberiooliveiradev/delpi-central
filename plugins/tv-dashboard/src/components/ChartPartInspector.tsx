import { FormSelectControl, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  applyMarkerStyleToAll,
  chartPartAllowsDelete,
  chartPartVisualPrimitive,
  chartPrimitiveSupportsFill,
  chartPrimitiveSupportsStroke,
  CHART_LEGEND_POSITION_OPTIONS,
  deleteChartPart,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  OFFICE_CHART_SERIES_COLOR,
  partsToChartOptions,
  resolveChartAreaStyle,
  resolvePlotAreaStyle,
  serializeChartPartRef,
  upsertChartPartState,
  type ComunicadoChartOptions,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  block: ComunicadoChartViewBlock;
};

function chartPartLabel(part: ComunicadoChartPartRef): string {
  switch (part.kind) {
    case "chartArea":
      return "Área do gráfico";
    case "plotArea":
      return "Área de plotagem";
    case "title":
      return "Título";
    case "legend":
      return "Legenda";
    case "series":
      return "Série (linha)";
    case "marker":
      return `Marcador ${part.pointIndex + 1}`;
    case "dataLabel":
      return `Rótulo ${part.pointIndex + 1}`;
    case "axis":
      return part.axis === "x" ? "Eixo X" : "Eixo Y";
    case "axisTitle":
      return part.axis === "x" ? "Título eixo X" : "Título eixo Y";
    case "grid":
      return "Grade";
    case "dataTable":
      return "Tabela de dados";
    default:
      return serializeChartPartRef(part);
  }
}

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
  const { selectedChartPart, clearChartPartSelection, beginEditChartPart, updateSelected } =
    useComunicadoEditor();

  if (!selectedChartPart) return null;

  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });
  const primitive = chartPartVisualPrimitive(selectedChartPart);
  const seriesColor = options.seriesColor ?? OFFICE_CHART_SERIES_COLOR;
  const partKey = serializeChartPartRef(selectedChartPart);
  const partState = block.chartParts?.[partKey];
  const canDelete = chartPartAllowsDelete(selectedChartPart);
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
    if (selectedChartPart.kind === "series" && patch.style?.stroke) {
      nextOptions.seriesColor = patch.style.stroke;
    }
    if (selectedChartPart.kind === "legend" && patch.content !== undefined) {
      nextOptions.seriesName = patch.content;
    }
    if (selectedChartPart.kind === "chartArea" && patch.style?.fill) {
      nextOptions.backgroundColor = patch.style.fill;
      nextOptions.theme = "light";
    }
    updateSelected({
      chartParts: nextParts,
      chartOptions: nextOptions,
    } as Partial<typeof block>);
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
      title={`Parte: ${chartPartLabel(selectedChartPart)}`}
      hint="Ajuste estilo e conteúdo desta parte. Del oculta a parte (não remove o gráfico)."
      defaultOpen
    >
      <div className="td-chart-part-inspector__actions">
        <button type="button" className="td-deck-btn td-deck-btn--ghost" onClick={clearChartPartSelection}>
          Limpar subseleção
        </button>
        {selectedChartPart.kind === "title" ? (
          <button
            type="button"
            className="td-deck-btn td-deck-btn--ghost"
            onClick={() => beginEditChartPart(block.id, selectedChartPart)}
          >
            Editar no palco
          </button>
        ) : null}
        {canDelete ? (
          <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={hideSelectedPart}>
            Excluir parte
          </button>
        ) : null}
      </div>

      {selectedChartPart.kind === "chartArea" || selectedChartPart.kind === "plotArea" ? (
        <>
          <DeckField id="td-chart-part-area-fill" label="Preenchimento">
            <TvRibbonColorPicker
              inline
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
              label="Contorno"
              value={
                selectedChartPart.kind === "chartArea" ? chartAreaStyle.stroke : plotAreaStyle.stroke
              }
              onChange={(color) => patchPart({ style: { stroke: color } })}
            />
          </DeckField>
          <DeckField id="td-chart-part-area-stroke-width" label="Espessura da borda">
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
          {selectedChartPart.kind === "chartArea" ? (
            <DeckField id="td-chart-part-area-radius" label="Cantos (px)">
              <NativeTextControl
                id="td-chart-part-area-radius"
                type="number"
                min={0}
                max={32}
                step={1}
                value={chartAreaStyle.borderRadius}
                onChange={(value) =>
                  patchPart({ style: { borderRadius: Math.max(0, Number(value) || 0) } })
                }
              />
            </DeckField>
          ) : null}
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
                persistOptions({ ...options, seriesColor: color });
                patchPart({ style: { stroke: color, fill: color } });
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
              selectedChartPart.axis === "x" ? (options.xAxisTitle ?? "") : (options.yAxisTitle ?? "")
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
              onChange={(color) => {
                persistOptions({ ...options, seriesColor: color });
                patchPart({ style: { stroke: color, fill: color } });
              }}
            />
          </DeckField>
          <DeckField id="td-chart-part-series-width" label="Espessura">
            <NativeTextControl
              id="td-chart-part-series-width"
              type="number"
              min={1}
              max={8}
              step={0.5}
              value={block.chartParts?.["series:0"]?.style?.strokeWidth ?? 2}
              onChange={(value) => patchPart({ style: { strokeWidth: Number(value) || 2 } })}
            />
          </DeckField>
        </>
      ) : null}

      {selectedChartPart.kind === "marker" && primitive && chartPrimitiveSupportsFill(primitive) ? (
        <>
          <DeckField id="td-chart-part-marker-fill" label="Preenchimento (ponto)">
            <TvRibbonColorPicker
              inline
              label="Cor do marcador"
              value={block.chartParts?.[partKey]?.style?.fill ?? seriesColor}
              onChange={(color) => patchPart({ style: { fill: color } })}
            />
          </DeckField>
          <DeckField id="td-chart-part-marker-stroke" label="Contorno">
            <TvRibbonColorPicker
              inline
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
