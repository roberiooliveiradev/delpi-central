import type { SeriesChartOptions, SeriesChartKind, SeriesChartPoint } from "../seriesChartOptions";
import type { SeriesChartLayout } from "./layout";

export type SeriesChartSharedProps = {
  layout: SeriesChartLayout;
  config: SeriesChartOptions;
  points: SeriesChartPoint[];
  seriesColor: string;
  valueFormat: NonNullable<SeriesChartOptions["valueFormat"]>;
};

export type SeriesChartKindProps = SeriesChartSharedProps & {
  chartType: SeriesChartKind;
};
