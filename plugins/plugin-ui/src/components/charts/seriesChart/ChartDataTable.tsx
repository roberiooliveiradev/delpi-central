import { formatSeriesChartValue, type SeriesChartValueFormat, type SeriesChartPoint } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartDataTableProps = {
  points: SeriesChartPoint[];
  seriesName: string;
  valueFormat: SeriesChartValueFormat;
  visible?: boolean;
};

export function ChartDataTable({ points, seriesName, valueFormat, visible = true }: ChartDataTableProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  return (
    <table className={cn.dataTable}>
      <thead>
        <tr>
          <th>Período</th>
          <th>{seriesName}</th>
        </tr>
      </thead>
      <tbody>
        {points.map((point, index) => (
          <tr key={`dt-${index}`}>
            <td>{String(point.label ?? index + 1)}</td>
            <td>{formatSeriesChartValue(Number(point.value), valueFormat ?? "auto")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
