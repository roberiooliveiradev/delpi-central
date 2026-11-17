import type { KeyboardEvent as ReactKeyboardEvent } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";
import {
  isSeriesChartFiniteValue,
  resolveSeriesCategoryColor,
  resolveValueScaleColor,
  resolveGoalThresholdColor,
  seriesValueExtent,
  type SeriesChartColorScale,
  type SeriesChartPoint,
} from "../seriesChartOptions";
import {
  chartPartDomProps,
  isChartPartRefEqual,
  type SeriesChartInteraction,
} from "../seriesChartParts";
import {
  seriesChartPointKey,
  type SeriesChartPointSelection,
} from "../seriesChartPointSelection";
import { resolveSeriesChartCategoryBarSlot } from "./layout";
import type { SeriesChartSharedProps } from "./types";
import { ensureSelectableBarSpan, resolveZeroBasedValueSpan } from "./zeroBasedBarGeometry";

export type ChartSeriesBarProps = Pick<SeriesChartSharedProps, "layout" | "points" | "seriesColor"> & {
  interaction?: SeriesChartInteraction | null;
  seriesIndex?: number;
  /** Posição no grupo visível. `seriesIndex` permanece o índice de chartParts. */
  layoutSeriesIndex?: number;
  /** Total de séries no grupo (barras lado a lado). Default 1 = ocupa a categoria inteira. */
  seriesCount?: number;
  /** Paleta por categoria / rampa semântica (série única). */
  categoryColors?: string[] | null;
  colorScale?: SeriesChartColorScale | null;
  /** Valor da linha de meta (`by_goal`). */
  goalValue?: number | null;
  /** Seleção de ponto/categoria (U14R2). Sem isto, paint idêntico ao legado. */
  pointSelection?: SeriesChartPointSelection | null;
};

/**
 * Colunas (vertical) ou barras (horizontal) cartesianas.
 * Com `seriesCount` > 1, divide o slot da categoria entre as séries (grouped).
 * Com `colorScale.mode === "by_value"` / `"by_goal"` (ou `categoryColors` na série única), cada barra tem cor própria.
 */
export function ChartSeriesBar({
  layout,
  points,
  seriesColor,
  interaction,
  seriesIndex = 0,
  layoutSeriesIndex,
  seriesCount = 1,
  categoryColors,
  colorScale,
  goalValue = null,
  pointSelection = null,
}: ChartSeriesBarProps) {
  const cn = useSeriesChartClasses();
  const { toY, axisMin, axisMax, orientation, toValueX } = layout;
  const ref = { kind: "series" as const, seriesIndex };
  const selected = isChartPartRefEqual(ref, interaction?.selectedPart);
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const categoryCount = Math.max(points.length, 1);
  const horizontal = orientation === "horizontal";
  const extent = seriesValueExtent(points.map((p) => p.value));
  const goalOk = goalValue != null && Number.isFinite(Number(goalValue));
  const usePerBarColor =
    seriesCount <= 1 &&
    (colorScale?.mode === "by_value" ||
      (colorScale?.mode === "by_goal" && goalOk) ||
      Boolean(categoryColors && categoryColors.length > 0));
  const pointSelectable = Boolean(pointSelection?.onPointSelect);
  const selectedKey = pointSelection?.selectedPointKey ?? null;

  const resolveFill = (point: (typeof points)[number], index: number): string => {
    if (!usePerBarColor) return seriesColor;
    const slotIndex =
      typeof point.sourceIndex === "number" && Number.isFinite(point.sourceIndex)
        ? point.sourceIndex
        : index;
    const value = Number(point.value) || 0;
    if (colorScale?.mode === "by_goal" && goalOk) {
      return resolveGoalThresholdColor({
        value,
        goal: Number(goalValue),
        polarity: colorScale.polarity ?? "high_is_good",
        fallbackColor: seriesColor,
      });
    }
    if (colorScale?.mode === "by_value" && categoryColors && categoryColors.length > 0) {
      return resolveValueScaleColor({
        value,
        min: extent.min,
        max: extent.max,
        colors: categoryColors,
        polarity: colorScale.polarity ?? "high_is_bad",
      });
    }
    return resolveSeriesCategoryColor(slotIndex, seriesColor, categoryColors);
  };

  const activatePoint = (point: SeriesChartPoint, index: number) => {
    if (!pointSelection?.onPointSelect) return;
    const key = seriesChartPointKey(point, index, pointSelection.pointKey);
    if (selectedKey != null && selectedKey === key) {
      pointSelection.onPointSelect(null, null);
      return;
    }
    pointSelection.onPointSelect(point, index);
  };

  const onPointKeyDown = (
    event: ReactKeyboardEvent<SVGGElement>,
    point: SeriesChartPoint,
    index: number,
  ) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    event.stopPropagation();
    activatePoint(point, index);
  };

  return (
    <g
      {...chartPartDomProps(ref, interaction?.selectedPart)}
      onPointerDown={
        interactive && !pointSelectable
          ? (event) => {
              event.stopPropagation();
              interaction?.onPartPointerDown?.(ref, event);
            }
          : undefined
      }
      onDoubleClick={
        interactive && !pointSelectable
          ? (event) => {
              event.stopPropagation();
              event.preventDefault();
              interaction?.onPartDoubleClick?.(ref, event);
            }
          : undefined
      }
    >
      {points.map((point, index) => {
        if (!isSeriesChartFiniteValue(point.value) && !pointSelectable) return null;
        const raw = isSeriesChartFiniteValue(point.value) ? Number(point.value) : 0;
        const value = Math.min(axisMax, Math.max(axisMin, raw));
        const slotIndex =
          typeof point.sourceIndex === "number" && Number.isFinite(point.sourceIndex)
            ? point.sourceIndex
            : index;
        const slot = resolveSeriesChartCategoryBarSlot({
          layout,
          categoryIndex: slotIndex,
          categoryCount,
          seriesIndex: layoutSeriesIndex ?? seriesIndex,
          seriesCount,
        });
        const fill = resolveFill(point, index);
        const key = seriesChartPointKey(point, index, pointSelection?.pointKey);
        const isSelected = selectedKey != null && selectedKey === key;
        const isDimmed = selectedKey != null && selectedKey !== key;
        const label = (point.label ?? "").trim() || `Categoria ${index + 1}`;
        const ariaLabel = `${label}: ${
          Number.isFinite(raw) ? raw.toLocaleString("pt-BR") : "—"
        }`;
        const barClass = [
          cn.seriesBar,
          selected && !pointSelectable ? `${cn.root}__part--selected` : "",
          pointSelectable && isSelected ? `${cn.root}__series-bar--selected` : "",
          pointSelectable && isDimmed ? `${cn.root}__series-bar--dimmed` : "",
        ]
          .filter(Boolean)
          .join(" ");

        const rectProps = horizontal && toValueX
          ? (() => {
              const span = resolveZeroBasedValueSpan(toValueX, value);
              const { start, size } = ensureSelectableBarSpan(
                span, value, pointSelectable ? 4 : 0, true,
              );
              return {
                x: start,
                y: slot.y,
                width: size,
                height: slot.height,
              };
            })()
          : (() => {
              // Negativos descem do zero e positivos sobem do zero.
              // A borda inferior do plot NÃO é a origem em escalas com negativos.
              const span = resolveZeroBasedValueSpan(toY, value);
              const { start, size } = ensureSelectableBarSpan(
                span, value, pointSelectable ? 4 : 0,
              );
              return {
                x: slot.x,
                y: start,
                width: slot.width,
                height: size,
              };
            })();

        if (!pointSelectable) {
          if (!isSeriesChartFiniteValue(point.value)) return null;
          return (
            <rect
              key={`bar-${seriesIndex}-${slotIndex}`}
              {...rectProps}
              fill={fill}
              rx={1}
              className={barClass}
            />
          );
        }

        return (
          <g
            key={`bar-${seriesIndex}-${slotIndex}`}
            role="button"
            tabIndex={0}
            aria-pressed={isSelected}
            aria-label={ariaLabel}
            data-point-key={key}
            style={{ cursor: "pointer", outline: "none" }}
            onClick={(event) => {
              event.stopPropagation();
              activatePoint(point, index);
            }}
            onKeyDown={(event) => onPointKeyDown(event, point, index)}
          >
            <rect {...rectProps} fill={fill} rx={1} className={barClass} />
          </g>
        );
      })}
    </g>
  );
}
