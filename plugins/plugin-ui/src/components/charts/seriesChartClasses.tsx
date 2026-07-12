import { createContext, useContext, type ReactNode } from "react";

export type SeriesChartClassNames = {
  root: string;
  rootEmpty: string;
  title: string;
  body: string;
  plotHost: string;
  svg: string;
  plotArea: string;
  plotAreaAxes: string;
  plotAreaChrome: string;
  axisLine: string;
  gridLine: string;
  gridLineVertical: string;
  tick: string;
  tickX: string;
  tickXRotated: string;
  tickY: string;
  axisTitle: string;
  axisTitleX: string;
  axisTitleY: string;
  dataLabel: string;
  seriesLine: string;
  seriesBar: string;
  seriesMarker: string;
  legend: string;
  legendTop: string;
  legendBottom: string;
  legendRight: string;
  legendItem: string;
  legendSwatch: string;
  dataTable: string;
};

export function seriesChartBemClasses(prefix = "delpi-ui-series-chart"): SeriesChartClassNames {
  return {
    root: prefix,
    rootEmpty: `${prefix} ${prefix}--empty`,
    title: `${prefix}__title`,
    body: `${prefix}__body`,
    plotHost: `${prefix}__plot-host`,
    svg: `${prefix}__svg`,
    plotArea: `${prefix}__plot-area`,
    plotAreaAxes: `${prefix}__plot-area--axes`,
    plotAreaChrome: `${prefix}__plot-area-chrome`,
    axisLine: `${prefix}__axis-line`,
    gridLine: `${prefix}__grid-line`,
    gridLineVertical: `${prefix}__grid-line--vertical`,
    tick: `${prefix}__tick`,
    tickX: `${prefix}__tick--x`,
    tickXRotated: `${prefix}__tick--x-rotated`,
    tickY: `${prefix}__tick--y`,
    axisTitle: `${prefix}__axis-title`,
    axisTitleX: `${prefix}__axis-title--x`,
    axisTitleY: `${prefix}__axis-title--y`,
    dataLabel: `${prefix}__data-label`,
    seriesLine: `${prefix}__series-line`,
    seriesBar: `${prefix}__series-bar`,
    seriesMarker: `${prefix}__series-marker`,
    legend: `${prefix}__legend`,
    legendTop: `${prefix}__legend--top`,
    legendBottom: `${prefix}__legend--bottom`,
    legendRight: `${prefix}__legend--right`,
    legendItem: `${prefix}__legend-item`,
    legendSwatch: `${prefix}__legend-swatch`,
    dataTable: `${prefix}__data-table`,
  };
}

/** TV dashboard — prefixo `tdp-series-chart` (native-screens.css). */
export function seriesChartTvClasses(): SeriesChartClassNames {
  return seriesChartBemClasses("tdp-series-chart");
}

const SeriesChartClassesContext = createContext<SeriesChartClassNames | null>(null);

export type SeriesChartClassesProviderProps = {
  prefix?: string;
  classNames?: SeriesChartClassNames;
  children: ReactNode;
};

export function SeriesChartClassesProvider({
  prefix,
  classNames,
  children,
}: SeriesChartClassesProviderProps) {
  const value = classNames ?? seriesChartBemClasses(prefix);
  return <SeriesChartClassesContext.Provider value={value}>{children}</SeriesChartClassesContext.Provider>;
}

export function useSeriesChartClasses(): SeriesChartClassNames {
  return useContext(SeriesChartClassesContext) ?? seriesChartBemClasses();
}
