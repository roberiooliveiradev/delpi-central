import { FormSelectControl } from "@delpi/plugin-ui/index";
import {
  CHART_ELEMENT_CATALOG,
  CHART_VALUE_FORMAT_OPTIONS,
  CHART_CATEGORY_LABEL_ROTATION_OPTIONS,
  CHART_CATEGORY_LABEL_OVERFLOW_OPTIONS,
  CHART_CATEGORY_LABEL_FORMAT_OPTIONS,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  toSeriesChartKind,
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
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ChartPartInspector } from "./ChartPartInspector";
import { InspectorElementRow } from "./InspectorElementRow";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  /** Quando true, omite aba/seção Série (já no SelectionSectionsHost). */
  omitSeries?: boolean;
};

function updateChartOptions(
  current: ComunicadoChartOptions | undefined,
  patch: Partial<ComunicadoChartOptions>,
): ComunicadoChartOptions {
  return { ...mergeComunicadoChartOptions(current), ...patch };
}

export function ChartViewOptionsInspector({ pane = false, omitSeries = false }: Props) {
  const { selected, updateSelected, selectChartPart, selectedChartPart } = useComunicadoEditor();

  if (!selected || selected.type !== "chart_view") return null;

  const block = selected as ComunicadoChartViewBlock;
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });
  const chartKind = toSeriesChartKind(block.chartType) ?? "line";
  const hasPartSelection = Boolean(selectedChartPart);

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<ComunicadoBlock>);
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
    } as Partial<ComunicadoBlock>);
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
        <>
          <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
            Clique no palco ou use a faixa Gráfico para ligar partes. Detalhes abrem ao selecionar a
            parte.
          </p>

          <div id="td-chart-pane-elements">
            <DeckPropertySection
              pane={pane}
              title="Elementos do gráfico"
              hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartElements}
              defaultOpen
            >
              <div className="td-chart-elements" role="group" aria-label="Elementos do gráfico">
                {elements.map((element) => {
                  const enabled = isChartElementEnabled(element.id, options);
                  const focused = isChartElementOpenForPart(element.id, selectedChartPart);
                  return (
                    <InspectorElementRow
                      key={element.id}
                      id={`td-chart-element-${element.id}`}
                      label={element.label}
                      hint={element.hint}
                      enabled={enabled}
                      focused={focused}
                      onToggle={(next) => toggleElement(element.id, next)}
                      onSelect={() => focusElement(element.id)}
                    />
                  );
                })}
              </div>
            </DeckPropertySection>
          </div>

          <div id="td-chart-pane-appearance">
            <DeckPropertySection
              pane={pane}
              title="Aparência"
              hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartAppearance}
              defaultOpen={false}
            >
              <DeckField
                id="td-chart-value-format"
                label="Formato dos valores"
                hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartValueFormat}
              >
                <FormSelectControl
                  id="td-chart-value-format"
                  ariaLabel="Formato dos valores"
                  value={options.valueFormat ?? "auto"}
                  onChange={(value) =>
                    setOptions({ valueFormat: value as ComunicadoChartOptions["valueFormat"] })
                  }
                  options={CHART_VALUE_FORMAT_OPTIONS.map((entry) => ({
                    value: entry.value,
                    label: entry.label,
                  }))}
                />
              </DeckField>
              <DeckField id="td-chart-decimal-places" label="Casas decimais">
                <FormSelectControl
                  id="td-chart-decimal-places"
                  ariaLabel="Casas decimais"
                  value={
                    options.decimalPlaces == null ? "auto" : String(options.decimalPlaces)
                  }
                  onChange={(value) =>
                    setOptions({
                      decimalPlaces: value === "auto" ? null : Number(value),
                    })
                  }
                  options={[
                    { value: "auto", label: "Automático" },
                    { value: "0", label: "0" },
                    { value: "1", label: "1" },
                    { value: "2", label: "2" },
                    { value: "3", label: "3" },
                    { value: "4", label: "4" },
                  ]}
                />
              </DeckField>
              <DeckField id="td-chart-category-rotation" label="Rotação dos rótulos (categoria)">
                <FormSelectControl
                  id="td-chart-category-rotation"
                  ariaLabel="Rotação dos rótulos de categoria"
                  value={
                    options.categoryLabelRotation == null
                      ? "auto"
                      : String(options.categoryLabelRotation)
                  }
                  onChange={(value) =>
                    setOptions({
                      categoryLabelRotation:
                        value === "auto"
                          ? "auto"
                          : (Number(value) as ComunicadoChartOptions["categoryLabelRotation"]),
                    })
                  }
                  options={CHART_CATEGORY_LABEL_ROTATION_OPTIONS.map((entry) => ({
                    value: entry.value,
                    label: entry.label,
                  }))}
                />
              </DeckField>
              <DeckField id="td-chart-category-overflow" label="Rótulos densos">
                <FormSelectControl
                  id="td-chart-category-overflow"
                  ariaLabel="Rótulos densos"
                  value={options.categoryLabelOverflow ?? "skip"}
                  onChange={(value) =>
                    setOptions({
                      categoryLabelOverflow:
                        value as ComunicadoChartOptions["categoryLabelOverflow"],
                    })
                  }
                  options={CHART_CATEGORY_LABEL_OVERFLOW_OPTIONS.map((entry) => ({
                    value: entry.value,
                    label: entry.label,
                  }))}
                />
              </DeckField>
              <DeckField id="td-chart-category-format" label="Formato da categoria">
                <FormSelectControl
                  id="td-chart-category-format"
                  ariaLabel="Formato da categoria"
                  value={options.categoryLabelFormat ?? "raw"}
                  onChange={(value) =>
                    setOptions({
                      categoryLabelFormat:
                        value as ComunicadoChartOptions["categoryLabelFormat"],
                    })
                  }
                  options={CHART_CATEGORY_LABEL_FORMAT_OPTIONS.map((entry) => ({
                    value: entry.value,
                    label: entry.label,
                  }))}
                />
              </DeckField>
            </DeckPropertySection>
          </div>

          {!omitSeries ? (
            <div id="td-chart-pane-series">
              <DeckPropertySection pane={pane} title="Série" defaultOpen={false}>
                <DeckField id="td-chart-series-color" label="Cor da série">
                  <TvRibbonColorPicker
                    inline
                    label="Cor da série"
                    value={options.seriesColor ?? OFFICE_CHART_SERIES_COLOR}
                    onChange={(color) => setOptions({ seriesColor: color })}
                  />
                </DeckField>
              </DeckPropertySection>
            </div>
          ) : null}
        </>
      ) : null}
    </>
  );
}
