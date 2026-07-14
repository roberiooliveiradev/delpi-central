import {
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  OFFICE_CHART_SERIES_COLOR,
  partsToChartOptions,
  type ComunicadoBlock,
  type ComunicadoChartOptions,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "../comunicadoEditorContext";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { DeckField } from "../deck/DeckField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

/**
 * Série do gráfico (cor principal) — seção tipada ribbon + painel.
 */
export function ChartSeriesSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedChartPart, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "chart_view") return null;
  /* Com parte selecionada o chrome da série fica em partFormat. */
  if (selectedChartPart) return null;

  const block = selected as ComunicadoChartViewBlock;
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });

  const setSeriesColor = (color: string) => {
    const nextOptions: ComunicadoChartOptions = {
      ...options,
      seriesColor: color,
    };
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  const picker = (
    <TvRibbonColorPicker
      inline={layout === "pane"}
      label="Cor da série"
      value={options.seriesColor ?? OFFICE_CHART_SERIES_COLOR}
      onChange={setSeriesColor}
    />
  );

  if (layout === "pane") {
    return (
      <div id="td-chart-pane-series">
        <SelectionPaneSection title="Série" defaultOpen={false}>
          <DeckField id="td-chart-series-color" label="Cor da série">
            {picker}
          </DeckField>
        </SelectionPaneSection>
      </div>
    );
  }

  return (
    <DeckRibbonGroup label="Série" hint="Cor principal da série de dados.">
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
        {picker}
      </div>
    </DeckRibbonGroup>
  );
}
