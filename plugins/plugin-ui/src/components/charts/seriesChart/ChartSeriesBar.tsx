import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import { resolveSeriesChartCategoryBarSlot } from "./layout";
import type { SeriesChartSharedProps } from "./types";

export type ChartSeriesBarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  /** Total de séries no grupo (barras lado a lado). Default 1 = ocupa a categoria inteira. */
  seriesCount?: number;
};

/**
 * Colunas (vertical) ou barras (horizontal) cartesianas.
 * Com `seriesCount` > 1, divide o slot da categoria entre as séries (grouped).
 */
export function ChartSeriesBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  seriesCount = 1,
}: ChartSeriesBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotH, toY, axisMin, axisMax, orientation, toValueX } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const baselineY = margin.top + plotH;
  const baselineX = margin.left;
  const categoryCount = Math.max(points.length, 1);
  const horizontal = orientation === "horizontal";

  return (
    <g
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
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
      {points.map((point, index) => {
        const raw = Number(point.value);
        const value = Number.isFinite(raw)
          ? Math.min(axisMax, Math.max(axisMin, raw))
          : axisMin;
        const slotIndex =
          typeof point.sourceIndex === "number" && Number.isFinite(point.sourceIndex)
            ? point.sourceIndex
            : index;
        const slot = resolveSeriesChartCategoryBarSlot({
          layout,
          categoryIndex: slotIndex,
          categoryCount,
          seriesIndex,
          seriesCount,
        });

        if (horizontal && toValueX) {
          const x0 = toValueX(Math.min(axisMin, 0));
          const x1 = toValueX(value);
          const x = Math.min(x0, x1);
          const width = Math.max(0, Math.abs(x1 - x0));
          return (
            <rect
              key={`hbar-${seriesIndex}-${slotIndex}`}
              x={x || baselineX}
              y={slot.y}
              width={width}
              height={slot.height}
              fill={seriesColor}
              rx={1}
              className={[cn.seriesBar, selected ? `${cn.root}__part--selected` : ""]
                .filter(Boolean)
                .join(" ")}
            />
          );
        }

        const y = toY(value);
        const height = Math.max(0, baselineY - y);
        return (
          <rect
            key={`bar-${seriesIndex}-${slotIndex}`}
            x={slot.x}
            y={y}
            width={slot.width}
            height={height}
            fill={seriesColor}
            rx={1}
            className={[cn.seriesBar, selected ? `${cn.root}__part--selected` : ""]
              .filter(Boolean)
              .join(" ")}
          />
        );
      })}
    </g>
  );
}
