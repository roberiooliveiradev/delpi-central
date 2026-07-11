import { ChartAxisLines } from "./ChartAxisLines";
import { ChartAxisX } from "./ChartAxisX";
import { ChartAxisY } from "./ChartAxisY";
import { ChartDataPoints } from "./ChartDataPoints";
import { ChartGrid } from "./ChartGrid";
import { ChartPlotArea } from "./ChartPlotArea";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartSeriesLine } from "./ChartSeriesLine";
import { ChartValueLabels } from "./ChartValueLabels";
import type { ChartPartsMap, SeriesChartInteraction } from "../seriesChartParts";
import type { SeriesChartKindProps } from "./types";

export type ChartPlotAreaGroupProps = SeriesChartKindProps & {
  showAxes: boolean;
  showGrid: boolean;
  showVerticalGrid: boolean;
  showMarkers: boolean;
  showDataLabels: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
  strokeWidth?: number;
};

export function ChartPlotAreaGroup({
  chartType,
  layout,
  config,
  points,
  seriesColor,
  valueFormat,
  showAxes,
  showGrid,
  showVerticalGrid,
  showMarkers,
  showDataLabels,
  interaction,
  chartParts,
  strokeWidth,
}: ChartPlotAreaGroupProps) {
  return (
    <>
      <ChartAxisY
        layout={layout}
        showLabels={showAxes && config.showYAxisLabels !== false}
        showTitle={config.showYAxisTitle === true}
        title={config.yAxisTitle}
        valueFormat={valueFormat}
      />

      <ChartGrid
        layout={layout}
        showHorizontal={showGrid}
        showVertical={showVerticalGrid}
        pointCount={points.length}
      />

      <ChartPlotArea layout={layout} showAxes={showAxes} />
      <ChartAxisLines layout={layout} visible={showAxes} />

      {chartType === "bar" ? (
        <ChartSeriesBar
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
        />
      ) : (
        <>
          <ChartSeriesLine
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            strokeWidth={strokeWidth}
            interaction={interaction}
            chartParts={chartParts}
          />
          <ChartDataPoints
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            visible={showMarkers}
            interaction={interaction}
            chartParts={chartParts}
          />
        </>
      )}

      <ChartValueLabels
        chartType={chartType}
        layout={layout}
        points={points}
        valueFormat={valueFormat}
        visible={showDataLabels}
        chartParts={chartParts}
      />

      <ChartAxisX
        layout={layout}
        points={points}
        showLabels={showAxes && config.showXAxisLabels !== false}
        showTitle={config.showXAxisTitle === true}
        title={config.xAxisTitle}
      />
    </>
  );
}
