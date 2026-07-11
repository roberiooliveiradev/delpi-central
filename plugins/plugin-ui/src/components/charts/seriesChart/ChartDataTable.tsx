import { useLayoutEffect, useRef, type CSSProperties } from "react";

import { formatSeriesChartValue, type SeriesChartValueFormat, type SeriesChartPoint } from "../seriesChartOptions";
import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  bindChartPartPointer,
  chartPartAllowsResize,
  clampChartPartFrame,
  getChartPartState,
  type ChartPartsMap,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { ChartPartResizeHandles } from "./ChartPartResizeHandles";

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
  selected: boolean,
): CSSProperties | undefined {
  if (!frame) {
    return selected ? { position: "relative", zIndex: 3 } : undefined;
  }
  return {
    position: "absolute",
    left: `${frame.x}%`,
    top: `${frame.y}%`,
    width: frame.w != null ? `${frame.w}%` : "auto",
    height: frame.h != null ? `${frame.h}%` : "auto",
    zIndex: 3,
    margin: 0,
    boxSizing: "border-box",
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
  const frame = getChartPartState(chartParts, ref)?.frame;
  const { selected, onPointerDown, onDoubleClick, ...dom } = bindChartPartPointer(ref, interaction);
  const frameStyle = partFrameStyle(frame, selected);
  const showResize = selected && chartPartAllowsResize(ref);
  const hostRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!showResize || frame?.w != null || !interaction?.onPartFrameChange || !hostRef.current) return;
    const chartRoot = hostRef.current.closest(".delpi-ui-series-chart, .tdp-series-chart");
    if (!chartRoot) return;
    const rect = chartRoot.getBoundingClientRect();
    const el = hostRef.current.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    interaction.onPartFrameChange(
      ref,
      clampChartPartFrame({
        x: ((el.left - rect.left) / rect.width) * 100,
        y: ((el.top - rect.top) / rect.height) * 100,
        w: Math.max(10, (el.width / rect.width) * 100),
        h: Math.max(8, (el.height / rect.height) * 100),
      }),
    );
  }, [showResize, frame?.w, interaction]);

  return (
    <div
      ref={hostRef}
      className={[
        cn.dataTable,
        frameStyle?.position === "absolute" ? `${cn.root}__part--framed` : "",
        selected ? `${cn.root}__part--selected` : "",
        showResize ? `${cn.root}__part--resizable` : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={frameStyle}
      {...dom}
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
    >
      <table className={`${cn.dataTable}__inner`}>
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
      <ChartPartResizeHandles
        visible={showResize}
        onResizePointerDown={(handle, event) => {
          interaction?.onPartResizePointerDown?.(ref, event, handle);
        }}
      />
    </div>
  );
}
