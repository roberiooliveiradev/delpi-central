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
 * Colunas cartesianas — topo via toY (domínio do eixo); base no fundo do plot.
 * Com `seriesCount` > 1, divide o slot da categoria entre as séries (grouped bars).
 *
 * Seleção: hit-target no `<g>` (série inteira); outline em todas as barras.
 * X alinha com rótulos via band scale (`toX` / `categoryBand*`) + `sourceIndex`.
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
  const { margin, plotH, toY, axisMin, axisMax } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const baseline = margin.top + plotH;
  const categoryCount = Math.max(points.length, 1);

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
        const { x, width: barW } = resolveSeriesChartCategoryBarSlot({
          layout,
          categoryIndex: slotIndex,
          categoryCount,
          seriesIndex,
          seriesCount,
        });
        const y = toY(value);
        const height = Math.max(0, baseline - y);

        return (
          <rect
            key={`bar-${seriesIndex}-${slotIndex}`}
            x={x}
            y={y}
            width={barW}
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
