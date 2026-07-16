import type { SeriesChartOptions, SeriesChartKind, SeriesChartPoint, SeriesChartSeriesSpec } from "../seriesChartOptions";
import type { SeriesChartLayout } from "./layout";

export type SeriesChartSharedProps = {
  layout: SeriesChartLayout;
  config: SeriesChartOptions;
  points: SeriesChartPoint[];
  seriesList?: SeriesChartSeriesSpec[];
  seriesColor: string;
  valueFormat: NonNullable<SeriesChartOptions["valueFormat"]>;
};

export type SeriesChartKindProps = SeriesChartSharedProps & {
  chartType: SeriesChartKind;
};
