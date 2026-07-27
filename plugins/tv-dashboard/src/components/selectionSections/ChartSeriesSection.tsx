import {
  mergeComunicadoChartOptions,
  type ComunicadoBlock,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  patchChartSeriesAppearance,
  resolveChartSeriesAppearanceColor,
  resolveChartSeriesColorIndex,
} from "../../utils/chartSeriesAppearance";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { TvRibbonColorPicker } from "../deck/TvRibbonColorPicker";
import { DeckField } from "../deck/DeckField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

/**
 * Cor da série/categoria — mesma fonte que plot e swatch da legenda.
 * Visível no bloco (série 0) ou com parte série / legenda / fatia selecionada.
 */
export function ChartSeriesSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedChartPart, updateSelected } = useComunicadoEditor();
  if (!selected || selected.type !== "chart_view") return null;

  if (
    selectedChartPart &&
    selectedChartPart.kind !== "series" &&
    selectedChartPart.kind !== "legend" &&
    selectedChartPart.kind !== "marker"
  ) {
    return null;
  }

  const block = selected as ComunicadoChartViewBlock;
  const seriesIndex = resolveChartSeriesColorIndex(selectedChartPart);
  const color = resolveChartSeriesAppearanceColor(block, seriesIndex);
  const label =
    selectedChartPart?.kind === "marker" ||
    (selectedChartPart?.kind === "series" && seriesIndex > 0)
      ? `Cor ${seriesIndex + 1}`
      : "Cor da série";

  const setSeriesColor = (nextColor: string) => {
    const appearance = patchChartSeriesAppearance(block, seriesIndex, { color: nextColor });
    updateSelected({
      ...(appearance.chartProjection ? { chartProjection: appearance.chartProjection } : {}),
      ...(appearance.chartParts ? { chartParts: appearance.chartParts } : {}),
      ...(appearance.chartOptions
        ? {
            chartOptions: mergeComunicadoChartOptions({
              ...block.chartOptions,
              ...appearance.chartOptions,
            }),
          }
        : {}),
    } as Partial<ComunicadoBlock>);
  };

  const picker = (
    <TvRibbonColorPicker
      inline={layout === "pane"}
      label={label}
      value={color}
      onChange={setSeriesColor}
    />
  );

  if (layout === "pane") {
    return (
      <div id="td-chart-pane-series">
        <SelectionPaneSection title="Série" hint={H.chartSeriesColor} defaultOpen={false}>
          <DeckField id="td-chart-series-color" label={label} hint={H.chartSeriesColor}>
            {picker}
          </DeckField>
        </SelectionPaneSection>
      </div>
    );
  }

  return (
    <DeckRibbonGroup groupId="chart-series" label="Série" hint={H.chartSeriesColor}>
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--color-pickers">
        {picker}
      </div>
    </DeckRibbonGroup>
  );
}
