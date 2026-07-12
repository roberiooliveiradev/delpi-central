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

/**
 * Colunas cartesianas — topo via toY (domínio do eixo); base no fundo do plot.
 * Valores fora do domínio são clampados para não furar a moldura.
 */
export function ChartSeriesBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
}: ChartSeriesBarProps) {
  const cn = useSeriesChartClasses();
  const { margin, plotW, plotH, toY, axisMin, axisMax } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const baseline = margin.top + plotH;

  return (
    <>
      {points.map((point, index) => {
        const raw = Number(point.value);
        const value = Number.isFinite(raw)
          ? Math.min(axisMax, Math.max(axisMin, raw))
          : axisMin;
        const barW = plotW / Math.max(points.length, 1);
        const gap = Math.min(barW * 0.2, 8);
        const width = Math.max(barW - gap, 2);
        const x = margin.left + index * barW + gap / 2;
        const y = toY(value);
        const height = Math.max(0, baseline - y);

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
    </>
  );
}
