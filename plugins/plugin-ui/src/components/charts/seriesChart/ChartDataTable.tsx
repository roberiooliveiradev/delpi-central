import { formatSeriesChartValue, type SeriesChartValueFormat, type SeriesChartPoint } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartDataTableProps = {
  points: SeriesChartPoint[];
  seriesName: string;
  valueFormat: SeriesChartValueFormat;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
};

export function ChartDataTable({
  points,
  seriesName,
  valueFormat,
  visible = true,
  interaction,
}: ChartDataTableProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const ref = { kind: "dataTable" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);

  return (
    <table
      className={[cn.dataTable, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
            }
          : undefined
      }
    >
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
