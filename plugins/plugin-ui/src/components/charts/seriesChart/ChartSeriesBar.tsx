import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesBarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
};

export function ChartSeriesBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
}: ChartSeriesBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, toY } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown);

  return (
    <>
      {points.map((point, index) => {
        const value = Number(point.value);
        const barW = plotW / Math.max(points.length, 1);
        const gap = Math.min(barW * 0.2, 8);
        const width = Math.max(barW - gap, 2);
        const x = margin.left + index * barW + gap / 2;
        const y = toY(value);
        const height = margin.top + plotH - y;

        return (
          <rect
            key={`bar-${index}`}
            x={x}
            y={y}
            width={width}
            height={height}
            fill={seriesColor}
            rx={1}
            className={[cn.seriesBar, selected ? `${cn.root}__part--selected` : ""].filter(Boolean).join(" ")}
            {...(index === 0 ? chartPartDomProps(ref, interaction?.selectedPart) : {})}
            onPointerDown={
              interactive
                ? (event) => {
                    event.stopPropagation();
                    interaction?.onPartPointerDown?.(ref, event);
                  }
                : undefined
            }
          />
        );
      })}
    </>
  );
}
