import { NativeSelectControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import {
  CHART_ELEMENT_CATALOG,
  CHART_LEGEND_POSITION_OPTIONS,
  CHART_VALUE_FORMAT_OPTIONS,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  chartOptionsToParts,
  chartTypeToLegacyDisplayMode,
  isChartElementApplicable,
  isChartElementEnabled,
  isChartElementOpenForPart,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  type ComunicadoChartOptions,
  type ComunicadoChartViewBlock,
  type ChartElementId,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ChartPartInspector } from "./ChartPartInspector";
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

function ChartElementPanel({
  elementId,
  enabled,
  open,
  onToggle,
  onSelect,
  children,
  label,
  hint,
}: {
  elementId: ChartElementId;
  enabled: boolean;
  open: boolean;
  onToggle: (next: boolean) => void;
  onSelect: () => void;
  children?: ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <details className="td-chart-element" open={open || enabled}>
      <summary className="td-chart-element__summary">
        <label className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <input
            type="checkbox"
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={(event) => onToggle(event.target.checked)}
          />
        </label>
        <button
          type="button"
          className="td-chart-element__label-btn"
          id={`td-chart-element-${elementId}`}
          onClick={(event) => {
            event.preventDefault();
            onSelect();
          }}
        >
          {label}
        </button>
        {hint ? <span className="td-chart-element__hint">{hint}</span> : null}
      </summary>
      {enabled && children ? <div className="td-chart-element__body">{children}</div> : null}
    </details>
  );
}

export function ChartViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected, selectChartPart, selectedChartPart } = useComunicadoEditor();
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

  const focusElement = (elementId: ChartElementId) => {
    const primary = chartElementPrimaryPartRef(elementId);
    if (primary) selectChartPart(block.id, primary);
  };

  const toggleElement = (elementId: ChartElementId, enabled: boolean) => {
    if (elementId === "series" && !enabled) {
      focusElement(elementId);
      return;
    }
    const result = applyChartElementVisibility(elementId, enabled, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<typeof selected>);
    if (enabled) {
      const primary = chartElementPrimaryPartRef(elementId);
      if (primary) selectChartPart(block.id, primary);
    }
  };

  const elements = CHART_ELEMENT_CATALOG.filter((entry) => isChartElementApplicable(entry, chartKind));

  return (
    <>
      <ChartPartInspector pane={pane} block={block} />

      <DeckPropertySection pane={pane} title="Elementos do gráfico" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartElements}>
        <div className="td-chart-elements" role="group" aria-label="Elementos do gráfico">
          {elements.map((element) => {
            const enabled = isChartElementEnabled(element.id, options);
            const open = isChartElementOpenForPart(element.id, selectedChartPart);
            return (
              <ChartElementPanel
                key={element.id}
                elementId={element.id}
                label={element.label}
                hint={element.hint}
                enabled={enabled}
                open={open}
                onToggle={(next) => toggleElement(element.id, next)}
                onSelect={() => focusElement(element.id)}
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
