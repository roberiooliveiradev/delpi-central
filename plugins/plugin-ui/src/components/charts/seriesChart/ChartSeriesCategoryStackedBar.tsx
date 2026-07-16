import { useSeriesChartClasses } from "../seriesChartClasses";
import type { SeriesChartSeriesSpec } from "../seriesChartOptions";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import type { SeriesChartLayout } from "./layout";

export type ChartSeriesCategoryStackedBarProps = {
  layout: SeriesChartLayout;
  seriesList: SeriesChartSeriesSpec[];
  resolveColor: (index: number, explicit?: string) => string;
  interaction?: SeriesChartInteraction | null;
};

/**
 * Barras empilhadas por categoria: cada índice de ponto é uma coluna;
 * cada item de `seriesList` é um segmento vertical (multi-série).
 */
export function ChartSeriesCategoryStackedBar({
  layout,
  seriesList,
  resolveColor,
  interaction,
}: ChartSeriesCategoryStackedBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, toY, axisMin } = layout;
  const categoryCount = Math.max(...seriesList.map((series) => series.points.length), 0);
  if (categoryCount === 0 || seriesList.length === 0) return null;

  const slotW = plotW / categoryCount;
  const groupPad = Math.min(slotW * 0.18, 8);
  const barW = Math.max(slotW - groupPad * 2, 2);

  return (
    <>
      {Array.from({ length: categoryCount }, (_, catIndex) => {
        let cumulative = 0;
        const x = margin.left + catIndex * slotW + groupPad;
        return (
          <g key={`stack-col-${catIndex}`}>
            {seriesList.map((series, seriesIndex) => {
              const point = series.points[catIndex];
              const raw = Number(point?.value);
              if (!Number.isFinite(raw) || raw <= 0) return null;
              const prev = cumulative;
              cumulative += Math.max(0, raw);
              const yTop = toY(cumulative);
              const yBottom = toY(Math.max(axisMin, prev));
              const height = Math.max(0, yBottom - yTop);
              const ref = { kind: "series" as const, seriesIndex };
              const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
              const interactive = Boolean(
                interaction?.onPartPointerDown || interaction?.onPartDoubleClick,
              );
              return (
                <rect
                  key={`stack-${seriesIndex}-${catIndex}`}
                  x={x}
                  y={yTop}
                  width={barW}
                  height={height}
                  fill={resolveColor(seriesIndex, series.color)}
                  stroke="#ffffff"
                  strokeWidth={0.6}
                  rx={1}
                  className={[cn.seriesStackedBar, selected ? `${cn.root}__part--selected` : ""]
                    .filter(Boolean)
                    .join(" ")}
                  {...(catIndex === 0 ? chartPartDomProps(ref, interaction?.selectedPart) : {})}
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
                />
              );
            })}
          </g>
        );
      })}
    </>
  );
}
