import { NativeCheckboxControl, NativeSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";
import {
  CHART_ELEMENT_CATALOG,
  CHART_LEGEND_POSITION_OPTIONS,
  CHART_VALUE_FORMAT_OPTIONS,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  chartTypeToLegacyDisplayMode,
  isChartElementApplicable,
  isChartElementEnabled,
  isChartElementOpenForPart,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  OFFICE_CHART_SERIES_COLOR,
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

/** Linha compacta de visibilidade — detalhes só quando a parte está focada (4M.5). */
function ChartElementRow({
  elementId,
  enabled,
  expanded,
  onToggle,
  onSelect,
  children,
  label,
  hint,
}: {
  elementId: ChartElementId;
  enabled: boolean;
  expanded: boolean;
  onToggle: (next: boolean) => void;
  onSelect: () => void;
  children?: ReactNode;
  label: string;
  hint?: string;
}) {
  const hasDetails = Boolean(children);
  const showBody = expanded && enabled && hasDetails;

  return (
    <div
      className={[
        "td-chart-element",
        "td-chart-element--row",
        showBody ? "td-chart-element--expanded" : null,
        expanded ? "td-chart-element--focused" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="td-chart-element__summary">
        <span className="td-chart-element__toggle" onClick={(event) => event.stopPropagation()}>
          <NativeCheckboxControl
            checked={enabled}
            aria-label={`Exibir ${label}`}
            onChange={onToggle}
          />
        </span>
        <button
          type="button"
          className="td-chart-element__label-btn"
          id={`td-chart-element-${elementId}`}
          title={hint}
          onClick={(event) => {
            event.preventDefault();
            onSelect();
          }}
        >
          {label}
        </button>
      </div>
      {showBody ? <div className="td-chart-element__body">{children}</div> : null}
    </div>
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
  const hasPartSelection = Boolean(selectedChartPart);

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
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
    if (
      (elementId === "series" || elementId === "chartArea" || elementId === "plotArea") &&
      !enabled
    ) {
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

      {!hasPartSelection ? (
        <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
          Clique no título, série, legenda ou área no palco para formatar a parte.
        </p>
      ) : null}

      <DeckPropertySection
        pane={pane}
        title="Elementos do gráfico"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartElements}
        defaultOpen={!hasPartSelection}
      >
        <div className="td-chart-elements" role="group" aria-label="Elementos do gráfico">
          {elements.map((element) => {
            const enabled = isChartElementEnabled(element.id, options);
            const expanded = isChartElementOpenForPart(element.id, selectedChartPart);
            return (
              <ChartElementRow
                key={element.id}
                elementId={element.id}
                label={element.label}
                hint={element.hint}
                enabled={enabled}
                expanded={expanded}
                onToggle={(next) => toggleElement(element.id, next)}
                onSelect={() => focusElement(element.id)}
              >
                {element.id === "chartTitle" ? (
                  <DeckField id="td-chart-title" label="Texto do título" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartTitle}>
                    <NativeTextControl
                      id="td-chart-title"
                      value={options.title ?? ""}
                      placeholder="Ex.: ROL"
                      onChange={(value) => setOptions({ title: value })}
                    />
                  </DeckField>
                ) : null}

                {element.id === "legend" ? (
                  <>
                    <DeckField id="td-chart-series-name" label="Nome da série" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartLegend}>
                      <NativeTextControl
                        id="td-chart-series-name"
                        value={options.seriesName ?? ""}
                        placeholder="Ex.: Receita"
                        onChange={(value) => setOptions({ seriesName: value })}
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
                      <NativeTextControl
                        id="td-chart-x-title"
                        value={options.xAxisTitle ?? ""}
                        placeholder="Ex.: Mês"
                        onChange={(value) => setOptions({ xAxisTitle: value, showXAxisTitle: true })}
                      />
                    </DeckField>
                    <DeckField id="td-chart-y-title" label="Título eixo Y">
                      <NativeTextControl
                        id="td-chart-y-title"
                        value={options.yAxisTitle ?? ""}
                        placeholder="Ex.: Valor (R$)"
                        onChange={(value) => setOptions({ yAxisTitle: value, showYAxisTitle: true })}
                      />
                    </DeckField>
                  </>
                ) : null}

                {element.id === "axes" ? (
                  <>
                    <DeckField id="td-chart-show-x-labels" label="Rótulos eixo X">
                      <NativeCheckboxControl
                        id="td-chart-show-x-labels"
                        checked={options.showXAxisLabels !== false}
                        label="Períodos e categorias"
                        onChange={(checked) => setOptions({ showXAxisLabels: checked })}
                      />
                    </DeckField>
                    <DeckField id="td-chart-show-y-labels" label="Rótulos eixo Y">
                      <NativeCheckboxControl
                        id="td-chart-show-y-labels"
                        checked={options.showYAxisLabels !== false}
                        label="Escala de valores"
                        onChange={(checked) => setOptions({ showYAxisLabels: checked })}
                      />
                    </DeckField>
                  </>
                ) : null}

                {element.id === "gridlines" ? (
                  <>
                    <DeckField id="td-chart-show-grid-h" label="Grade horizontal">
                      <NativeCheckboxControl
                        id="td-chart-show-grid-h"
                        checked={options.showGrid !== false}
                        label="Linhas horizontais"
                        onChange={(checked) => setOptions({ showGrid: checked })}
                      />
                    </DeckField>
                    <DeckField id="td-chart-show-grid-v" label="Grade vertical">
                      <NativeCheckboxControl
                        id="td-chart-show-grid-v"
                        checked={Boolean(options.showVerticalGrid)}
                        label="Linhas verticais"
                        onChange={(checked) => setOptions({ showVerticalGrid: checked })}
                      />
                    </DeckField>
                  </>
                ) : null}
              </ChartElementRow>
            );
          })}
        </div>
      </DeckPropertySection>

      <DeckPropertySection
        pane={pane}
        title="Aparência"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartAppearance}
        defaultOpen={!hasPartSelection}
      >
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
            value={options.seriesColor ?? OFFICE_CHART_SERIES_COLOR}
            onChange={(color) => setOptions({ seriesColor: color })}
          />
        </DeckField>
      </DeckPropertySection>
    </>
  );
}
