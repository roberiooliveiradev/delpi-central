import { NativeSelectControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import {
  CHART_ELEMENT_CATALOG,
  CHART_LEGEND_POSITION_OPTIONS,
  CHART_VALUE_FORMAT_OPTIONS,
  chartOptionsToParts,
  chartTypeToLegacyDisplayMode,
  isChartElementApplicable,
  isChartElementEnabled,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  serializeChartPartRef,
  setChartElementEnabled,
  upsertChartPartState,
  type ComunicadoChartOptions,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
  type ChartElementId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

function updateChartOptions(
  current: ComunicadoChartOptions | undefined,
  patch: Partial<ComunicadoChartOptions>,
): ComunicadoChartOptions {
  return { ...mergeComunicadoChartOptions(current), ...patch };
}

function chartPartLabel(part: ComunicadoChartPartRef): string {
  switch (part.kind) {
    case "title":
      return "Título";
    case "legend":
      return "Legenda";
    case "series":
      return "Série";
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

function ChartElementPanel({
  elementId,
  enabled,
  onToggle,
  children,
  label,
  hint,
}: {
  elementId: ChartElementId;
  enabled: boolean;
  onToggle: (next: boolean) => void;
  children?: ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <details className="td-chart-element" open={enabled}>
      <summary className="td-chart-element__summary">
        <label className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <input
            type="checkbox"
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={(event) => onToggle(event.target.checked)}
          />
        </label>
        <span className="td-chart-element__label" id={`td-chart-element-${elementId}`}>
          {label}
        </span>
        {hint ? <span className="td-chart-element__hint">{hint}</span> : null}
      </summary>
      {enabled && children ? <div className="td-chart-element__body">{children}</div> : null}
    </details>
  );
}

export function ChartViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected, selectedChartPart, clearChartPartSelection } = useComunicadoEditor();
  if (!selected || selected.type !== "chart_view") return null;

  const block = selected as ComunicadoChartViewBlock;
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });
  const chartKind = chartTypeToLegacyDisplayMode(block.chartType) === "bar_chart" ? "bar" : "line";

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: chartOptionsToParts(nextOptions),
    } as Partial<typeof selected>);
  };

  const setOptions = (patch: Partial<ComunicadoChartOptions>) => {
    persistOptions(updateChartOptions(block.chartOptions, patch));
  };

  const patchSelectedPart = (patch: {
    content?: string;
    style?: { fill?: string; stroke?: string; markerRadius?: number };
  }) => {
    if (!selectedChartPart) return;
    const nextParts = upsertChartPartState(block.chartParts, selectedChartPart, patch);
    const nextOptions = mergeComunicadoChartOptions({
      ...block.chartOptions,
      ...partsToChartOptions(nextParts),
    });
    updateSelected({ chartParts: nextParts, chartOptions: nextOptions } as Partial<typeof selected>);
  };

  const toggleElement = (elementId: ChartElementId, enabled: boolean) => {
    setOptions(setChartElementEnabled(elementId, enabled));
  };

  const elements = CHART_ELEMENT_CATALOG.filter((entry) => isChartElementApplicable(entry, chartKind));

  return (
    <>
      {selectedChartPart ? (
        <DeckPropertySection
          pane={pane}
          title={`Parte: ${chartPartLabel(selectedChartPart)}`}
          hint="Clique em outro elemento do gráfico no palco ou limpe a seleção."
        >
          <button type="button" className="td-deck-btn td-deck-btn--ghost" onClick={clearChartPartSelection}>
            Limpar subseleção
          </button>
          {selectedChartPart.kind === "title" ? (
            <DeckField id="td-chart-part-title" label="Texto do título">
              <input
                id="td-chart-part-title"
                type="text"
                value={options.title ?? ""}
                placeholder="Ex.: ROL"
                onChange={(event) => setOptions({ title: event.target.value, showTitle: true })}
              />
            </DeckField>
          ) : null}
          {selectedChartPart.kind === "series" || selectedChartPart.kind === "legend" ? (
            <DeckField id="td-chart-part-series-color" label="Cor da série">
              <TvRibbonColorPicker
                inline
                label="Cor da série"
                value={options.seriesColor ?? "#0d7a8c"}
                onChange={(color) => setOptions({ seriesColor: color })}
              />
            </DeckField>
          ) : null}
          {selectedChartPart.kind === "marker" ? (
            <DeckField id="td-chart-part-marker-fill" label="Cor do marcador">
              <TvRibbonColorPicker
                inline
                label="Cor do marcador"
                value={options.seriesColor ?? "#0d7a8c"}
                onChange={(color) => patchSelectedPart({ style: { fill: color } })}
              />
            </DeckField>
          ) : null}
          {selectedChartPart.kind === "legend" ? (
            <DeckField id="td-chart-part-series-name" label="Nome da série">
              <input
                id="td-chart-part-series-name"
                type="text"
                value={options.seriesName ?? ""}
                onChange={(event) => setOptions({ seriesName: event.target.value })}
              />
            </DeckField>
          ) : null}
        </DeckPropertySection>
      ) : null}

      <DeckPropertySection pane={pane} title="Elementos do gráfico" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartElements}>
        <div className="td-chart-elements" role="group" aria-label="Elementos do gráfico">
          {elements.map((element) => {
            const enabled = isChartElementEnabled(element.id, options);
            return (
              <ChartElementPanel
                key={element.id}
                elementId={element.id}
                label={element.label}
                hint={element.hint}
                enabled={enabled}
                onToggle={(next) => toggleElement(element.id, next)}
              >
                {element.id === "chartTitle" ? (
                  <DeckField id="td-chart-title" label="Texto do título" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartTitle}>
                    <input
                      id="td-chart-title"
                      type="text"
                      value={options.title ?? ""}
                      placeholder="Ex.: ROL"
                      onChange={(event) => setOptions({ title: event.target.value })}
                    />
                  </DeckField>
                ) : null}

                {element.id === "legend" ? (
                  <>
                    <DeckField id="td-chart-series-name" label="Nome da série" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartLegend}>
                      <input
                        id="td-chart-series-name"
                        type="text"
                        value={options.seriesName ?? ""}
                        placeholder="Ex.: Receita"
                        onChange={(event) => setOptions({ seriesName: event.target.value })}
                      />
                    </DeckField>
                    <DeckField id="td-chart-legend-position" label="Posição">
                      <NativeSelectControl
                        id="td-chart-legend-position"
                        value={options.legendPosition ?? "bottom"}
                        onChange={(value) =>
                          setOptions({ legendPosition: value as ComunicadoChartOptions["legendPosition"] })
                        }
                        options={CHART_LEGEND_POSITION_OPTIONS.filter((entry) => entry.value !== "hidden").map(
                          (entry) => ({ value: entry.value, label: entry.label }),
                        )}
                      />
                    </DeckField>
                  </>
                ) : null}

                {element.id === "axisTitles" ? (
                  <>
                    <DeckField id="td-chart-x-title" label="Título eixo X">
                      <input
                        id="td-chart-x-title"
                        type="text"
                        value={options.xAxisTitle ?? ""}
                        placeholder="Ex.: Mês"
                        onChange={(event) => setOptions({ xAxisTitle: event.target.value, showXAxisTitle: true })}
                      />
                    </DeckField>
                    <DeckField id="td-chart-y-title" label="Título eixo Y">
                      <input
                        id="td-chart-y-title"
                        type="text"
                        value={options.yAxisTitle ?? ""}
                        placeholder="Ex.: Valor (R$)"
                        onChange={(event) => setOptions({ yAxisTitle: event.target.value, showYAxisTitle: true })}
                      />
                    </DeckField>
                  </>
                ) : null}

                {element.id === "axes" ? (
                  <>
                    <DeckField id="td-chart-show-x-labels" label="Rótulos eixo X">
                      <label className="td-deck-inspector__checkbox">
                        <input
                          id="td-chart-show-x-labels"
                          type="checkbox"
                          checked={options.showXAxisLabels !== false}
                          onChange={(event) => setOptions({ showXAxisLabels: event.target.checked })}
                        />
                        <span>Períodos e categorias</span>
                      </label>
                    </DeckField>
                    <DeckField id="td-chart-show-y-labels" label="Rótulos eixo Y">
                      <label className="td-deck-inspector__checkbox">
                        <input
                          id="td-chart-show-y-labels"
                          type="checkbox"
                          checked={options.showYAxisLabels !== false}
                          onChange={(event) => setOptions({ showYAxisLabels: event.target.checked })}
                        />
                        <span>Escala de valores</span>
                      </label>
                    </DeckField>
                  </>
                ) : null}

                {element.id === "gridlines" ? (
                  <>
                    <DeckField id="td-chart-show-grid-h" label="Grade horizontal">
                      <label className="td-deck-inspector__checkbox">
                        <input
                          id="td-chart-show-grid-h"
                          type="checkbox"
                          checked={options.showGrid !== false}
                          onChange={(event) => setOptions({ showGrid: event.target.checked })}
                        />
                        <span>Linhas horizontais</span>
                      </label>
                    </DeckField>
                    <DeckField id="td-chart-show-grid-v" label="Grade vertical">
                      <label className="td-deck-inspector__checkbox">
                        <input
                          id="td-chart-show-grid-v"
                          type="checkbox"
                          checked={Boolean(options.showVerticalGrid)}
                          onChange={(event) => setOptions({ showVerticalGrid: event.target.checked })}
                        />
                        <span>Linhas verticais</span>
                      </label>
                    </DeckField>
                  </>
                ) : null}
              </ChartElementPanel>
            );
          })}
        </div>
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Aparência" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartAppearance}>
        <DeckField id="td-chart-value-format" label="Formato dos valores">
          <NativeSelectControl
            id="td-chart-value-format"
            value={options.valueFormat ?? "auto"}
            onChange={(value) => setOptions({ valueFormat: value as ComunicadoChartOptions["valueFormat"] })}
            options={CHART_VALUE_FORMAT_OPTIONS.map((entry) => ({
              value: entry.value,
              label: entry.label,
            }))}
          />
        </DeckField>
        <DeckField id="td-chart-series-color" label="Cor da série">
          <TvRibbonColorPicker
            inline
            label="Cor da série"
            value={options.seriesColor ?? "#0d7a8c"}
            onChange={(color) => setOptions({ seriesColor: color })}
          />
        </DeckField>
      </DeckPropertySection>
    </>
  );
}
