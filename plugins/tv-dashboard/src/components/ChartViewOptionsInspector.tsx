import { useState } from "react";
import { FormSelectControl } from "@delpi/plugin-ui/index";
import {
  CHART_ELEMENT_CATALOG,
  CHART_VALUE_FORMAT_OPTIONS,
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
import { ChartColumn, Layers, Palette } from "lucide-react";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ChartPartInspector } from "./ChartPartInspector";
import { InspectorElementRow } from "./InspectorElementRow";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
};

const CHART_PANE_ICONS = [
  { id: "elements", label: "Elementos", Icon: Layers },
  { id: "appearance", label: "Aparência", Icon: Palette },
  { id: "series", label: "Série", Icon: ChartColumn },
] as const;

function updateChartOptions(
  current: ComunicadoChartOptions | undefined,
  patch: Partial<ComunicadoChartOptions>,
): ComunicadoChartOptions {
  return { ...mergeComunicadoChartOptions(current), ...patch };
}

export function ChartViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected, selectChartPart, selectedChartPart } = useComunicadoEditor();
  const [paneIcon, setPaneIcon] = useState<(typeof CHART_PANE_ICONS)[number]["id"]>("elements");

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

  const scrollToPane = (id: (typeof CHART_PANE_ICONS)[number]["id"]) => {
    setPaneIcon(id);
    document.getElementById(`td-chart-pane-${id}`)?.scrollIntoView({ block: "nearest" });
  };

  const elements = CHART_ELEMENT_CATALOG.filter((entry) => isChartElementApplicable(entry, chartKind));

  return (
    <>
      <ChartPartInspector pane={pane} block={block} />

      {!hasPartSelection ? (
        <>
          <div className="td-format-pane-icons" role="tablist" aria-label="Categorias do gráfico">
            {CHART_PANE_ICONS.map(({ id, label, Icon }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={paneIcon === id}
                aria-label={label}
                title={label}
                className={[
                  "td-format-pane-icons__btn",
                  paneIcon === id ? "td-format-pane-icons__btn--active" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => scrollToPane(id)}
              >
                <Icon size={16} aria-hidden="true" />
              </button>
            ))}
          </div>

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
              defaultOpen
            >
              <DeckField id="td-chart-value-format" label="Formato dos valores">
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
            </DeckPropertySection>
          </div>

          <div id="td-chart-pane-series">
            <DeckPropertySection pane={pane} title="Série" defaultOpen>
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
        </>
      ) : null}
    </>
  );
}
