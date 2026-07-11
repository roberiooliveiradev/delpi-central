import type { CSSProperties } from "react";

import { formatSeriesChartValue, type SeriesChartValueFormat, type SeriesChartPoint } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  getChartPartState,
  isChartPartRefEqual,
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

function partFrameStyle(
  frame: { x: number; y: number; w?: number; h?: number } | undefined,
): CSSProperties | undefined {
  if (!frame) return undefined;
  return {
    position: "absolute",
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: frame.w != null ? `${frame.w}%` : "auto",
    height: frame.h != null ? `${frame.h}%` : "auto",
    zIndex: 3,
    margin: 0,
  };
}

export function ChartDataTable({
  points,
  seriesName,
  valueFormat,
  visible = true,
  interaction,
  chartParts,
}: ChartDataTableProps) {
  const cn = useSeriesChartClasses();
  if (!visible) return null;

  const ref = { kind: "dataTable" as const };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const frame = getChartPartState(chartParts, ref)?.frame;
  const frameStyle = partFrameStyle(frame);

  return (
    <table
      className={[
        cn.dataTable,
        frameStyle ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={frameStyle}
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
              if (selected) {
                interaction?.onPartMovePointerDown?.(ref, event);
              }
            }
          : undefined
      }
      onDoubleClick={
        interactive
          ? (event) => {
              event.stopPropagation();
              event.preventDefault();
              interaction?.onPartDoubleClick?.(ref, event);
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
