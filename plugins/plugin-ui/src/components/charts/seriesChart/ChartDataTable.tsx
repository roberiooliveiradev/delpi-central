import type { SeriesChartValueFormat, SeriesChartPoint } from "../seriesChartOptions";
import { formatSeriesChartValue } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";

export type ChartDataTableProps = {
  points: SeriesChartPoint[];
  seriesName: string;
  valueFormat: SeriesChartValueFormat;
  visible?: boolean;
  interaction?: SeriesChartInteraction | null;
  chartParts?: ChartPartsMap | null;
};

/**
 * Grade de dados abaixo do plot (fluxo normal).
 * Não usa `frame` absoluto — evita sobrepor o gráfico (bug de tabela “flutuante”).
 */
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
  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction);

  return (
    <div
      className={[cn.dataTable, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <table className={`${cn.dataTable}__inner`}>
        <thead>
          <tr>
            <th scope="col">Período</th>
            <th scope="col">{seriesName}</th>
          </tr>
        </thead>
        <tbody>
          {points.map((point, index) => {
            const period = String(point.label ?? "").trim() || String(index + 1);
            return (
              <tr key={`dt-${index}`}>
                <td>{period}</td>
                <td>{formatSeriesChartValue(Number(point.value), valueFormat ?? "auto")}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
