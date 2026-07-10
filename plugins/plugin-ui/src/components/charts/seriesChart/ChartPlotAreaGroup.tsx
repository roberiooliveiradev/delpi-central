import { ChartAxisLines } from "./ChartAxisLines";
import { ChartAxisX } from "./ChartAxisX";
import { ChartAxisY } from "./ChartAxisY";
import { ChartDataPoints } from "./ChartDataPoints";
import { ChartGrid } from "./ChartGrid";
import { ChartPlotArea } from "./ChartPlotArea";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartSeriesLine } from "./ChartSeriesLine";
import { ChartValueLabels } from "./ChartValueLabels";
import type { SeriesChartKindProps } from "./types";

export type ChartPlotAreaGroupProps = SeriesChartKindProps & {
  showAxes: boolean;
  showGrid: boolean;
  showVerticalGrid: boolean;
  showMarkers: boolean;
  showDataLabels: boolean;
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
        <ChartSeriesBar layout={layout} points={points} seriesColor={seriesColor} />
      ) : (
        <>
          <ChartSeriesLine layout={layout} points={points} seriesColor={seriesColor} />
          <ChartDataPoints layout={layout} points={points} seriesColor={seriesColor} visible={showMarkers} />
        </>
      )}

      <ChartValueLabels
        chartType={chartType}
        layout={layout}
        points={points}
        valueFormat={valueFormat}
        visible={showDataLabels}
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
