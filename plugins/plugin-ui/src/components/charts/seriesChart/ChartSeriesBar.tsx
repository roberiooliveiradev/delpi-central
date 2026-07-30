import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  resolveSeriesCategoryColor,
  resolveValueScaleColor,
  seriesValueExtent,
  type SeriesChartColorScale,
} from "../seriesChartOptions";
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
  /** Paleta por categoria / rampa semântica (série única). */
  categoryColors?: string[] | null;
  colorScale?: SeriesChartColorScale | null;
};

/**
 * Colunas (vertical) ou barras (horizontal) cartesianas.
 * Com `seriesCount` > 1, divide o slot da categoria entre as séries (grouped).
 * Com `colorScale.mode === "by_value"` (ou `categoryColors` na série única), cada barra tem cor própria.
 */
export function ChartSeriesBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  seriesCount = 1,
  categoryColors,
  colorScale,
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
  const extent = seriesValueExtent(points.map((p) => p.value));
  const usePerBarColor =
    seriesCount <= 1 &&
    (colorScale?.mode === "by_value" || Boolean(categoryColors && categoryColors.length > 0));

  const resolveFill = (point: (typeof points)[number], index: number): string => {
    if (!usePerBarColor) return seriesColor;
    const slotIndex =
      typeof point.sourceIndex === "number" && Number.isFinite(point.sourceIndex)
        ? point.sourceIndex
        : index;
    if (colorScale?.mode === "by_value" && categoryColors && categoryColors.length > 0) {
      return resolveValueScaleColor({
        value: Number(point.value) || 0,
        min: extent.min,
        max: extent.max,
        colors: categoryColors,
        polarity: colorScale.polarity ?? "high_is_bad",
      });
    }
    return resolveSeriesCategoryColor(slotIndex, seriesColor, categoryColors);
  };

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
        const fill = resolveFill(point, index);

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
              fill={fill}
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
            fill={fill}
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
