import { ChartAxisLines } from "./ChartAxisLines";
import { ChartAxisX } from "./ChartAxisX";
import { ChartAxisY } from "./ChartAxisY";
import { ChartDataPoints } from "./ChartDataPoints";
import { ChartGrid } from "./ChartGrid";
import { ChartPlotArea } from "./ChartPlotArea";
import { ChartSeriesArea } from "./ChartSeriesArea";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartSeriesLine } from "./ChartSeriesLine";
import { ChartSeriesPie } from "./ChartSeriesPie";
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
  /** Rosca: raio interno relativo (só `pie`). */
  pieInnerRadiusRatio?: number;
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
  pieInnerRadiusRatio = 0,
}: ChartPlotAreaGroupProps) {
  const isPie = chartType === "pie";
  const cartesianAxes = showAxes && !isPie;
  const cartesianGrid = showGrid && !isPie;

  return (
    <>
      {!isPie ? (
        <ChartAxisY
          layout={layout}
          showLabels={cartesianAxes && config.showYAxisLabels !== false}
          showTitle={config.showYAxisTitle === true}
          title={config.yAxisTitle}
          valueFormat={valueFormat}
          interaction={interaction}
        />
      ) : null}

      {!isPie ? (
        <ChartGrid
          layout={layout}
          showHorizontal={cartesianGrid}
          showVertical={showVerticalGrid && !isPie}
          pointCount={points.length}
          interaction={interaction}
        />
      ) : null}

      <ChartPlotArea
        layout={layout}
        showAxes={cartesianAxes}
        interaction={interaction}
        chartParts={chartParts}
      />
      {!isPie ? <ChartAxisLines layout={layout} visible={cartesianAxes} interaction={interaction} /> : null}

      {chartType === "bar" ? (
        <ChartSeriesBar
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
        />
      ) : null}

      {chartType === "area" ? (
        <ChartSeriesArea
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          strokeWidth={strokeWidth}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "pie" ? (
        <ChartSeriesPie
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
          innerRadiusRatio={pieInnerRadiusRatio}
        />
      ) : null}

      {chartType === "combo" ? (
        <>
          <ChartSeriesBar
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            interaction={interaction}
            seriesIndex={0}
          />
          <ChartSeriesLine
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            strokeWidth={strokeWidth}
            interaction={interaction}
            chartParts={chartParts}
            seriesIndex={1}
          />
          <ChartDataPoints
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            visible={showMarkers}
            interaction={interaction}
            chartParts={chartParts}
            seriesIndex={1}
          />
        </>
      ) : null}

      {chartType === "line" ? (
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
      ) : null}

      {chartType === "area" && showMarkers ? (
        <ChartDataPoints
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          visible={showMarkers}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {!isPie ? (
        <ChartValueLabels
          chartType={chartType}
          layout={layout}
          points={points}
          valueFormat={valueFormat}
          visible={showDataLabels}
          chartParts={chartParts}
          interaction={interaction}
        />
      ) : null}

      {!isPie ? (
        <ChartAxisX
          layout={layout}
          points={points}
          showLabels={cartesianAxes && config.showXAxisLabels !== false}
          showTitle={config.showXAxisTitle === true}
          title={config.xAxisTitle}
          interaction={interaction}
        />
      ) : null}
    </>
  );
}
