import { NativeSelectControl } from "@delpi/plugin-ui/index";
import {
  CHART_LEGEND_POSITION_OPTIONS,
  CHART_VALUE_FORMAT_OPTIONS,
  mergeComunicadoChartOptions,
  type ComunicadoChartOptions,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useComunicadoEditor } from "./comunicadoEditorContext";
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

export function ChartViewOptionsInspector({ pane = false }: Props) {
  const { selected, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "chart_view") return null;

  const block = selected as ComunicadoChartViewBlock;
  const options = mergeComunicadoChartOptions(block.chartOptions);

  const setOptions = (patch: Partial<ComunicadoChartOptions>) => {
    updateSelected({ chartOptions: updateChartOptions(block.chartOptions, patch) } as Partial<typeof selected>);
  };

  return (
    <DeckPropertySection pane={pane} title="Gráfico" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartOptions}>
      <DeckField id="td-chart-title" label="Título" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartTitle}>
        <input
          id="td-chart-title"
          type="text"
          value={options.title ?? ""}
          placeholder="Ex.: ROL"
          onChange={(event) => setOptions({ title: event.target.value })}
        />
      </DeckField>
      <DeckField id="td-chart-show-title" label="Exibir título">
        <label className="td-deck-inspector__checkbox">
          <input
            id="td-chart-show-title"
            type="checkbox"
            checked={options.showTitle !== false}
            onChange={(event) => setOptions({ showTitle: event.target.checked })}
          />
          <span>Mostrar título no gráfico</span>
        </label>
      </DeckField>
      <DeckField id="td-chart-series-name" label="Nome da série" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartLegend}>
        <input
          id="td-chart-series-name"
          type="text"
          value={options.seriesName ?? ""}
          placeholder="Ex.: Receita"
          onChange={(event) => setOptions({ seriesName: event.target.value })}
        />
      </DeckField>
      <DeckField id="td-chart-show-legend" label="Legenda">
        <label className="td-deck-inspector__checkbox">
          <input
            id="td-chart-show-legend"
            type="checkbox"
            checked={options.showLegend !== false}
            onChange={(event) => setOptions({ showLegend: event.target.checked })}
          />
          <span>Exibir legenda</span>
        </label>
      </DeckField>
      <DeckField id="td-chart-legend-position" label="Posição da legenda">
        <NativeSelectControl
          id="td-chart-legend-position"
          value={options.legendPosition ?? "bottom"}
          onChange={(value) =>
            setOptions({ legendPosition: value as ComunicadoChartOptions["legendPosition"] })
          }
          options={CHART_LEGEND_POSITION_OPTIONS.map((entry) => ({
            value: entry.value,
            label: entry.label,
          }))}
        />
      </DeckField>
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
      <DeckField id="td-chart-x-title" label="Título eixo X">
        <input
          id="td-chart-x-title"
          type="text"
          value={options.xAxisTitle ?? ""}
          onChange={(event) => setOptions({ xAxisTitle: event.target.value })}
        />
      </DeckField>
      <DeckField id="td-chart-y-title" label="Título eixo Y">
        <input
          id="td-chart-y-title"
          type="text"
          value={options.yAxisTitle ?? ""}
          onChange={(event) => setOptions({ yAxisTitle: event.target.value })}
        />
      </DeckField>
      <DeckField id="td-chart-show-x-labels" label="Rótulos eixo X">
        <label className="td-deck-inspector__checkbox">
          <input
            id="td-chart-show-x-labels"
            type="checkbox"
            checked={options.showXAxisLabels !== false}
            onChange={(event) => setOptions({ showXAxisLabels: event.target.checked })}
          />
          <span>Exibir períodos/categorias</span>
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
          <span>Exibir escala de valores</span>
        </label>
      </DeckField>
      <DeckField id="td-chart-show-data-labels" label="Rótulos de dados" hint={TV_DASHBOARD_HELP_TOOLTIPS.data.chartDataLabels}>
        <label className="td-deck-inspector__checkbox">
          <input
            id="td-chart-show-data-labels"
            type="checkbox"
            checked={Boolean(options.showDataLabels)}
            onChange={(event) => setOptions({ showDataLabels: event.target.checked })}
          />
          <span>Valor em cada ponto/barra</span>
        </label>
      </DeckField>
      <DeckField id="td-chart-show-grid" label="Grade">
        <label className="td-deck-inspector__checkbox">
          <input
            id="td-chart-show-grid"
            type="checkbox"
            checked={options.showGrid !== false}
            onChange={(event) => setOptions({ showGrid: event.target.checked })}
          />
          <span>Linhas horizontais de referência</span>
        </label>
      </DeckField>
      <DeckField id="td-chart-series-color" label="Cor da série">
        <input
          id="td-chart-series-color"
          type="color"
          value={options.seriesColor ?? "#0d7a8c"}
          onChange={(event) => setOptions({ seriesColor: event.target.value })}
        />
      </DeckField>
    </DeckPropertySection>
  );
}
