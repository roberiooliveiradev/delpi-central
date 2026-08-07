import { useId } from "react";

import { orderSeriesIndicesForOverlappingPaint } from "../seriesChartPaintOrder";
import { ChartAxisLines } from "./ChartAxisLines";
import { ChartAxisX } from "./ChartAxisX";
import { ChartAxisY } from "./ChartAxisY";
import { ChartDataPoints } from "./ChartDataPoints";
import { ChartGoalLine } from "./ChartGoalLine";
import { ChartGrid } from "./ChartGrid";
import { ChartPlotArea } from "./ChartPlotArea";
import { ChartSeriesBar } from "./ChartSeriesBar";
import { ChartSeriesBubble } from "./ChartSeriesBubble";
import { ChartSeriesCategoryStackedBar } from "./ChartSeriesCategoryStackedBar";
import { ChartSeriesFunnel } from "./ChartSeriesFunnel";
import { ChartSeriesHistogram } from "./ChartSeriesHistogram";
import { ChartSeriesLine } from "./ChartSeriesLine";
import { ChartSeriesPie } from "./ChartSeriesPie";
import { ChartSeriesRadar } from "./ChartSeriesRadar";
import { ChartSeriesScatter } from "./ChartSeriesScatter";
import { ChartSeriesStackedBar } from "./ChartSeriesStackedBar";
import { ChartSeriesWaterfall } from "./ChartSeriesWaterfall";
import { ChartSeriesArea } from "./ChartSeriesArea";
import { ChartValueLabels } from "./ChartValueLabels";
import type { SeriesChartDataLabelsResolved } from "../seriesChartDataLabels";
import {
  resolveSeriesPaintColor,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartKindProps } from "./types";

export type ChartPlotAreaGroupProps = SeriesChartKindProps & {
  showAxes: boolean;
  showGrid: boolean;
  showVerticalGrid: boolean;
  showGoalLine?: boolean;
  goalLineValue?: number | null;
  showMarkers: boolean;
  showDataLabels: boolean;
  dataLabels?: SeriesChartDataLabelsResolved | null;
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
  seriesList,
  seriesColor,
  valueFormat,
  showAxes,
  showGrid,
  showVerticalGrid,
  showGoalLine = false,
  goalLineValue = null,
  showMarkers,
  showDataLabels,
  dataLabels = null,
  interaction,
  chartParts,
  strokeWidth,
  pieInnerRadiusRatio = 0,
}: ChartPlotAreaGroupProps) {
  const smoothLines = Boolean(config.smoothLines);
  const skipCartesian = NON_CARTESIAN.has(chartType);
  const cartesianAxes = showAxes && !skipCartesian;
  const cartesianGrid = showGrid && !skipCartesian;
  const goalValue =
    showGoalLine && goalLineValue != null && Number.isFinite(Number(goalLineValue))
      ? Number(goalLineValue)
      : null;
  const clipRawId = useId().replace(/:/g, "");
  const plotClipId = `delpi-series-plot-clip-${clipRawId}`;

  const resolveSeriesColor = (index: number, explicit?: string) =>
    resolveSeriesPaintColor({
      seriesIndex: index,
      explicit,
      seriesColor,
      categoryColors: config.categoryColors,
      parts: chartParts,
    });

  const multiLine =
    (chartType === "line" || chartType === "area") &&
    seriesList &&
    seriesList.length > 1;
  const multiBar =
    (chartType === "bar" || chartType === "horizontal_bar") &&
    seriesList &&
    seriesList.length > 1;
  const multiStacked = chartType === "stacked_bar" && seriesList && seriesList.length > 1;

  const series = (
    <>
      {chartType === "bar" || chartType === "horizontal_bar" ? (
        multiBar && seriesList ? (
          <>
            {seriesList.map((entry, index) => (
              <ChartSeriesBar
                key={`series-bar-${entry.name}-${index}`}
                layout={layout}
                points={entry.points}
                seriesColor={resolveSeriesColor(index, entry.color)}
                interaction={interaction}
                seriesIndex={index}
                seriesCount={seriesList.length}
              />
            ))}
          </>
        ) : (
          <ChartSeriesBar
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            interaction={interaction}
            categoryColors={config.categoryColors}
            colorScale={config.colorScale}
            goalValue={goalValue}
          />
        )
      ) : null}

      {chartType === "stacked_bar" ? (
        multiStacked && seriesList ? (
          <ChartSeriesCategoryStackedBar
            layout={layout}
            seriesList={seriesList}
            resolveColor={resolveSeriesColor}
            interaction={interaction}
          />
        ) : (
          <ChartSeriesStackedBar
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            interaction={interaction}
            chartParts={chartParts}
            categoryColors={config.categoryColors}
            colorScale={config.colorScale}
            goalValue={goalValue}
          />
        )
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
          colorScale={config.colorScale}
          goalValue={goalValue}
        />
      ) : null}

      {chartType === "area" && !multiLine ? (
        <ChartSeriesArea
          layout={layout}
          points={points}
          seriesColor={seriesColor}
          strokeWidth={strokeWidth}
          smooth={smoothLines}
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
          colorScale={config.colorScale}
          goalValue={goalValue}
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
            categoryColors={config.categoryColors}
            colorScale={config.colorScale}
            goalValue={goalValue}
          />
          <ChartSeriesLine
            layout={layout}
            points={points}
            seriesColor={seriesColor}
            strokeWidth={strokeWidth}
            smooth={smoothLines}
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
        multiLine && seriesList ? (
          <>
            {seriesList.map((series, index) => {
              const color = resolveSeriesColor(index, series.color);
              return (
                <g key={`series-line-${series.name}-${index}`}>
                  <ChartSeriesLine
                    layout={layout}
                    points={series.points}
                    seriesColor={color}
                    strokeWidth={strokeWidth}
                    smooth={smoothLines}
                    plotOn={series.plotOn}
                    interaction={interaction}
                    chartParts={chartParts}
                    seriesIndex={index}
                  />
                  <ChartDataPoints
                    layout={layout}
                    points={series.points}
                    seriesColor={color}
                    visible={showMarkers}
                    interaction={interaction}
                    chartParts={chartParts}
                    seriesIndex={index}
                    plotOn={series.plotOn}
                  />
                </g>
              );
            })}
          </>
        ) : (
          <>
            <ChartSeriesLine
              layout={layout}
              points={points}
              seriesColor={seriesColor}
              strokeWidth={strokeWidth}
              smooth={smoothLines}
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
        )
      ) : null}

      {chartType === "area" && multiLine && seriesList ? (
        <>
          {orderSeriesIndicesForOverlappingPaint(seriesList).map((index) => {
            const series = seriesList[index]!;
            const color = resolveSeriesColor(index, series.color);
            return (
              <g key={`series-area-${series.name}-${index}`}>
                <ChartSeriesArea
                  layout={layout}
                  points={series.points}
                  seriesColor={color}
                  strokeWidth={strokeWidth}
                  smooth={smoothLines}
                  interaction={interaction}
                  chartParts={chartParts}
                  seriesIndex={index}
                />
                {showMarkers ? (
                  <ChartDataPoints
                    layout={layout}
                    points={series.points}
                    seriesColor={color}
                    visible={showMarkers}
                    interaction={interaction}
                    chartParts={chartParts}
                    seriesIndex={index}
                  />
                ) : null}
              </g>
            );
          })}
        </>
      ) : null}

      {chartType === "area" && !multiLine && showMarkers ? (
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
          chartParts={chartParts}
        />
      ) : null}

      {!skipCartesian && goalValue != null ? (
        <ChartGoalLine
          layout={layout}
          value={goalValue}
          visible
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {!skipCartesian ? (
        <ChartAxisY
          layout={layout}
          showLabels={cartesianAxes && config.showYAxisLabels !== false}
          showTitle={config.showYAxisTitle !== false}
          title={config.yAxisTitle}
          valueFormat={valueFormat}
          decimalPlaces={config.decimalPlaces}
          points={points}
          categoryLabelFormat={config.categoryLabelFormat}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

      {!skipCartesian ? (
        <ChartAxisLines
          layout={layout}
          visible={cartesianAxes}
          showX={cartesianAxes && config.showXAxisLabels !== false}
          showY={cartesianAxes && config.showYAxisLabels !== false}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}

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

      {showDataLabels && multiBar && seriesList ? (
        seriesList.map((entry, index) => (
          <ChartValueLabels
            key={`labels-bar-${entry.name}-${index}`}
            chartType={chartType}
            layout={layout}
            points={entry.points}
            valueFormat={valueFormat}
            config={config}
            visible={showDataLabels}
            chartParts={chartParts}
            interaction={interaction}
            seriesIndex={index}
            seriesCount={seriesList.length}
            seriesName={entry.name}
            dataLabels={dataLabels}
          />
        ))
      ) : showDataLabels && multiLine && seriesList ? (
        seriesList.map((entry, index) => (
          <ChartValueLabels
            key={`labels-line-${entry.name}-${index}`}
            chartType={chartType}
            layout={layout}
            points={entry.points}
            valueFormat={valueFormat}
            config={config}
            visible={showDataLabels}
            chartParts={chartParts}
            interaction={interaction}
            seriesIndex={index}
            seriesName={entry.name}
            dataLabels={dataLabels}
          />
        ))
      ) : showDataLabels && !(multiStacked && seriesList) ? (
        <ChartValueLabels
          chartType={chartType}
          layout={layout}
          points={points}
          valueFormat={valueFormat}
          config={config}
          visible={showDataLabels}
          chartParts={chartParts}
          interaction={interaction}
          pieInnerRadiusRatio={pieInnerRadiusRatio}
          dataLabels={dataLabels}
        />
      ) : null}

      {!skipCartesian ? (
        <ChartAxisX
          layout={layout}
          points={points}
          showLabels={cartesianAxes && config.showXAxisLabels !== false}
          showTitle={config.showXAxisTitle !== false}
          title={config.xAxisTitle}
          valueFormat={valueFormat}
          decimalPlaces={config.decimalPlaces}
          categoryLabelFormat={config.categoryLabelFormat}
          interaction={interaction}
          chartParts={chartParts}
        />
      ) : null}
    </>
  );
}
