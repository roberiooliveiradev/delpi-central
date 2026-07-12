import { NativeCheckboxControl, NativeSelectControl } from "@delpi/plugin-ui/index";
import {
  CHART_ELEMENT_CATALOG,
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

/** Linha de visibilidade — detalhe de formato fica só no ChartPartInspector (4M.7). */
function ChartElementRow({
  elementId,
  enabled,
  focused,
  onToggle,
  onSelect,
  label,
  hint,
}: {
  elementId: ChartElementId;
  enabled: boolean;
  focused: boolean;
  onToggle: (next: boolean) => void;
  onSelect: () => void;
  label: string;
  hint?: string;
}) {
  return (
    <div
      className={["td-chart-element", "td-chart-element--row", focused ? "td-chart-element--focused" : null]
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
        <>
          <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
            Clique no palco ou use a faixa Gráfico para ligar partes. Detalhes abrem ao selecionar a
            parte.
          </p>

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
                  <ChartElementRow
                    key={element.id}
                    elementId={element.id}
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

          <DeckPropertySection
            pane={pane}
            title="Aparência"
            hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartAppearance}
            defaultOpen
          >
            <DeckField id="td-chart-value-format" label="Formato dos valores">
              <NativeSelectControl
                id="td-chart-value-format"
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
      ) : null}
    </>
  );
}
