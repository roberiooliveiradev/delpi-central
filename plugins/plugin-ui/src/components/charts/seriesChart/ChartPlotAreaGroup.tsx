import { useId } from "react";

import { ChartAxisLines } from "./ChartAxisLines";
import { ChartAxisX } from "./ChartAxisX";
import { ChartAxisY } from "./ChartAxisY";
import { ChartDataPoints } from "./ChartDataPoints";
import { ChartGrid } from "./ChartGrid";
import { ChartPlotArea } from "./ChartPlotArea";
import { ChartSeriesArea } from "./ChartSeriesArea";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartSeriesBubble } from "./ChartSeriesBubble";
import { ChartSeriesFunnel } from "./ChartSeriesFunnel";
import { ChartSeriesHistogram } from "./ChartSeriesHistogram";
import { ChartSeriesLine } from "./ChartSeriesLine";
import { ChartSeriesPie } from "./ChartSeriesPie";
import { ChartSeriesRadar } from "./ChartSeriesRadar";
import { ChartSeriesScatter } from "./ChartSeriesScatter";
import { ChartSeriesStackedBar } from "./ChartSeriesStackedBar";
import { ChartSeriesWaterfall } from "./ChartSeriesWaterfall";
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

const NON_CARTESIAN: ReadonlySet<SeriesChartKindProps["chartType"]> = new Set([
  "pie",
  "radar",
  "funnel",
]);

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
  const skipCartesian = NON_CARTESIAN.has(chartType);
  const cartesianAxes = showAxes && !skipCartesian;
  const cartesianGrid = showGrid && !skipCartesian;
  const clipRawId = useId().replace(/:/g, "");
  const plotClipId = `delpi-series-plot-clip-${clipRawId}`;

  const series = (
    <>
      {chartType === "bar" ? (
        <ChartSeriesBar
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
        />
      ) : null}

      {chartType === "stacked_bar" ? (
        <ChartSeriesStackedBar
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
          categoryColors={config.categoryColors}
        />
      ) : null}

      {chartType === "histogram" ? (
        <ChartSeriesHistogram
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "scatter" ? (
        <ChartSeriesScatter
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "bubble" ? (
        <ChartSeriesBubble
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "radar" ? (
        <ChartSeriesRadar
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "waterfall" ? (
        <ChartSeriesWaterfall
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {chartType === "funnel" ? (
        <ChartSeriesFunnel
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          interaction={interaction}
          chartParts={chartParts}
          categoryColors={config.categoryColors}
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
          categoryColors={config.categoryColors}
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
    </>
  );

  return (
    <>
      <ChartPlotArea
        layout={layout}
        showAxes={cartesianAxes}
        interaction={interaction}
        chartParts={chartParts}
      />

      {!skipCartesian ? (
        <ChartGrid
          layout={layout}
          showHorizontal={cartesianGrid}
          showVertical={showVerticalGrid && !skipCartesian}
          pointCount={points.length}
          interaction={interaction}
        />
      ) : null}

      {!skipCartesian ? (
        <ChartAxisY
          layout={layout}
          showLabels={cartesianAxes && config.showYAxisLabels !== false}
          showTitle={config.showYAxisTitle !== false}
          title={config.yAxisTitle}
          valueFormat={valueFormat}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {!skipCartesian ? <ChartAxisLines layout={layout} visible={cartesianAxes} interaction={interaction} /> : null}

      {!skipCartesian ? (
        <>
          <defs>
            <clipPath id={plotClipId}>
              <rect
                x={layout.margin.left}
                y={layout.margin.top}
                width={layout.plotW}
                height={layout.plotH}
              />
            </clipPath>
          </defs>
          <g clipPath={`url(#${plotClipId})`}>{series}</g>
        </>
      ) : (
        series
      )}

      {!skipCartesian ? (
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

      {!skipCartesian ? (
        <ChartAxisX
          layout={layout}
          points={points}
          showLabels={cartesianAxes && config.showXAxisLabels !== false}
          showTitle={config.showXAxisTitle !== false}
          title={config.xAxisTitle}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}
    </>
  );
}
