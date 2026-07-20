import { useState, type ReactNode } from "react";

import {
  clampImpactEffortScore,
  resolveImpactEffortQuadrant,
  type ImpactEffortAxisLabels,
  type ImpactEffortPoint,
  type ImpactEffortQuadrantDescriptions,
  type ImpactEffortQuadrantLabels,
  DEFAULT_IMPACT_EFFORT_AXIS_LABELS,
  DEFAULT_IMPACT_EFFORT_QUADRANT_DESCRIPTIONS,
  DEFAULT_IMPACT_EFFORT_QUADRANT_LABELS,
} from "./impactEffortTypes";
import {
  impactEffortMatrixBemClasses,
  quadrantClassName,
  type ImpactEffortMatrixClassNames,
} from "./impactEffortMatrixClasses";
import { resolveActivePoint, resolveDisplayScores } from "./impactEffortMatrixLayout";

const PLOT = { x0: 14, y0: 6, w: 82, h: 82 };

function toPlotX(esforco: number): number {
  return PLOT.x0 + (clampImpactEffortScore(esforco) / 100) * PLOT.w;
}

function toPlotY(impacto: number): number {
  return PLOT.y0 + PLOT.h - (clampImpactEffortScore(impacto) / 100) * PLOT.h;
}

function formatScore(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
}

export type ImpactEffortMatrixProps = {
  points: ImpactEffortPoint[];
  activePointId?: string | null;
  threshold?: number;
  onPointSelect?: (point: ImpactEffortPoint) => void;
  quadrantLabels?: ImpactEffortQuadrantLabels;
  axisLabels?: ImpactEffortAxisLabels;
  classNames?: ImpactEffortMatrixClassNames;
  className?: string;
  emptyMessage?: string;
  ariaLabel?: string;
};

export function ImpactEffortMatrix({
  points,
  activePointId,
  threshold = 50,
  onPointSelect,
  quadrantLabels = DEFAULT_IMPACT_EFFORT_QUADRANT_LABELS,
  axisLabels = DEFAULT_IMPACT_EFFORT_AXIS_LABELS,
  classNames = impactEffortMatrixBemClasses(),
  className,
  emptyMessage = "Nenhuma revisão comparável para exibir.",
  ariaLabel = "Matriz impacto por esforço",
}: ImpactEffortMatrixProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const visiblePoints = points.filter((p) => !p.muted || p.id === activePointId);
  const thresholdX = toPlotX(threshold);
  const thresholdY = toPlotY(threshold);
  const activePoint = resolveActivePoint(points, activePointId);
  const hoveredPoint = hoveredId ? points.find((point) => point.id === hoveredId) : undefined;

  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  if (visiblePoints.length === 0) {
    return (
      <div className={rootClass} role="img" aria-label={ariaLabel}>
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  const hoverDisplay = hoveredPoint
    ? resolveDisplayScores(
        hoveredPoint.impacto,
        hoveredPoint.esforco,
        hoveredPoint.quadrante,
        threshold
      )
    : null;
  const hoverQuadrant = hoveredPoint
    ? hoveredPoint.quadrante ??
      resolveImpactEffortQuadrant(hoveredPoint.impacto, hoveredPoint.esforco, threshold)
    : null;

  return (
    <div className={rootClass}>
      <div className="delpi-ui-impact-effort-matrix__plot-shell">
        <svg
          className={classNames.plot}
          viewBox="0 0 100 100"
          role="img"
          aria-label={ariaLabel}
          preserveAspectRatio="xMidYMid meet"
        >
          <QuadrantRect
            className={quadrantClassName(classNames, "fill_in")}
            labelClassName={classNames.quadrantLabel}
            x={PLOT.x0}
            y={thresholdY}
            width={thresholdX - PLOT.x0}
            height={PLOT.y0 + PLOT.h - thresholdY}
            label={quadrantLabels.fill_in}
          />
          <QuadrantRect
            className={quadrantClassName(classNames, "quick_win")}
            labelClassName={classNames.quadrantLabel}
            x={PLOT.x0}
            y={PLOT.y0}
            width={thresholdX - PLOT.x0}
            height={thresholdY - PLOT.y0}
            label={quadrantLabels.quick_win}
          />
          <QuadrantRect
            className={quadrantClassName(classNames, "rethink")}
            labelClassName={classNames.quadrantLabel}
            x={thresholdX}
            y={thresholdY}
            width={PLOT.x0 + PLOT.w - thresholdX}
            height={PLOT.y0 + PLOT.h - thresholdY}
            label={quadrantLabels.rethink}
          />
          <QuadrantRect
            className={quadrantClassName(classNames, "strategic")}
            labelClassName={classNames.quadrantLabel}
            x={thresholdX}
            y={PLOT.y0}
            width={PLOT.x0 + PLOT.w - thresholdX}
            height={thresholdY - PLOT.y0}
            label={quadrantLabels.strategic}
          />

          <line
            className={classNames.axisLine}
            x1={PLOT.x0}
            y1={PLOT.y0 + PLOT.h}
            x2={PLOT.x0 + PLOT.w}
            y2={PLOT.y0 + PLOT.h}
          />
          <line
            className={classNames.axisLine}
            x1={PLOT.x0}
            y1={PLOT.y0}
            x2={PLOT.x0}
            y2={PLOT.y0 + PLOT.h}
          />
          <line
            className={classNames.thresholdLine}
            x1={thresholdX}
            y1={PLOT.y0}
            x2={thresholdX}
            y2={PLOT.y0 + PLOT.h}
          />
          <line
            className={classNames.thresholdLine}
            x1={PLOT.x0}
            y1={thresholdY}
            x2={PLOT.x0 + PLOT.w}
            y2={thresholdY}
          />

          <text
            className={`${classNames.axisLabel} ${classNames.axisLabelEffort}`}
            x={PLOT.x0 + PLOT.w / 2}
            y={99}
            textAnchor="middle"
            fontSize={3.6}
          >
            {axisLabels.esforco}
          </text>
          <text
            className={`${classNames.axisLabel} ${classNames.axisLabelImpact}`}
            x={2}
            y={PLOT.y0 + PLOT.h / 2}
            textAnchor="middle"
            fontSize={3.6}
            transform={`rotate(-90 2 ${PLOT.y0 + PLOT.h / 2})`}
          >
            {axisLabels.impacto}
          </text>

          {points.map((point) => {
            const display = resolveDisplayScores(point.impacto, point.esforco, point.quadrante, threshold);
            const cx = toPlotX(display.esforco);
            const cy = toPlotY(display.impacto);
            const isActive = point.id === activePointId;
            const pointClass = [
              classNames.point,
              isActive ? classNames.pointActive : "",
              point.muted ? classNames.pointMuted : "",
            ]
              .filter(Boolean)
              .join(" ");
            const pointStyle = point.accentColor
              ? { stroke: point.accentColor, fill: point.accentColor }
              : undefined;
            const interactive = Boolean(onPointSelect && !point.muted);
            const hoverHandlers = {
              onMouseEnter: () => setHoveredId(point.id),
              onMouseLeave: () => setHoveredId((current) => (current === point.id ? null : current)),
              onFocus: () => setHoveredId(point.id),
              onBlur: () => setHoveredId((current) => (current === point.id ? null : current)),
            };

            return (
              <g key={point.id}>
                <circle
                  className={[
                    "delpi-ui-impact-effort-matrix__point-hit",
                    point.muted ? "delpi-ui-impact-effort-matrix__point-hit--muted" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  cx={cx}
                  cy={cy}
                  r={6}
                  {...hoverHandlers}
                  onClick={interactive ? () => onPointSelect?.(point) : undefined}
                  onKeyDown={
                    interactive
                      ? (event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onPointSelect?.(point);
                          }
                        }
                      : undefined
                  }
                  role={interactive ? "button" : undefined}
                  tabIndex={interactive ? 0 : undefined}
                  aria-label={`${point.label}, impacto ${point.impacto}, esforço ${point.esforco}`}
                />
                <circle
                  className={pointClass}
                  style={pointStyle}
                  cx={cx}
                  cy={cy}
                  r={isActive ? 3.2 : 2.6}
                  pointerEvents="none"
                />
              </g>
            );
          })}
        </svg>

        {hoveredPoint && hoverDisplay && hoverQuadrant ? (
          <div
            className={classNames.tooltip}
            role="tooltip"
            style={{
              left: `${toPlotX(hoverDisplay.esforco)}%`,
              top: `${toPlotY(hoverDisplay.impacto)}%`,
            }}
          >
            <strong className="delpi-ui-impact-effort-matrix__tooltip-title">{hoveredPoint.label}</strong>
            <span className="delpi-ui-impact-effort-matrix__tooltip-scores">
              Impacto {formatScore(hoveredPoint.impacto)} · Esforço {formatScore(hoveredPoint.esforco)}
            </span>
            <span className="delpi-ui-impact-effort-matrix__tooltip-quadrant">
              {quadrantLabels[hoverQuadrant]}
            </span>
          </div>
        ) : null}
      </div>

      {activePoint && !activePoint.muted ? (
        <p className={classNames.activeCaption} title={activePoint.label}>
          {activePoint.label}
        </p>
      ) : null}
    </div>
  );
}

function QuadrantRect({
  className,
  labelClassName,
  x,
  y,
  width,
  height,
  label,
}: {
  className: string;
  labelClassName: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
}) {
  if (width <= 0 || height <= 0) return null;
  return (
    <g aria-hidden="true">
      <rect className={className} x={x} y={y} width={width} height={height} rx={0.8} />
      <text
        className={labelClassName}
        x={x + width / 2}
        y={y + height / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={3.2}
      >
        {label}
      </text>
    </g>
  );
}

export type ImpactEffortMatrixLegendProps = {
  quadrantLabels?: ImpactEffortQuadrantLabels;
  quadrantDescriptions?: ImpactEffortQuadrantDescriptions;
  className?: string;
  children?: ReactNode;
};

export function ImpactEffortMatrixLegend({
  quadrantLabels = DEFAULT_IMPACT_EFFORT_QUADRANT_LABELS,
  quadrantDescriptions = DEFAULT_IMPACT_EFFORT_QUADRANT_DESCRIPTIONS,
  className,
  children,
}: ImpactEffortMatrixLegendProps) {
  const items: Array<{ key: keyof ImpactEffortQuadrantLabels; classSuffix: string }> = [
    { key: "quick_win", classSuffix: "quick-win" },
    { key: "strategic", classSuffix: "strategic" },
    { key: "fill_in", classSuffix: "fill-in" },
    { key: "rethink", classSuffix: "rethink" },
  ];

  return (
    <ul
      className={[
        "delpi-ui-impact-effort-matrix__legend",
        "delpi-ui-impact-effort-matrix__legend--explained",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {items.map((item) => (
        <li key={item.key} className="delpi-ui-impact-effort-matrix__legend-item">
          <span
            className={`delpi-ui-impact-effort-matrix__legend-swatch delpi-ui-impact-effort-matrix__legend-swatch--${item.classSuffix}`}
            aria-hidden="true"
          />
          <span className="delpi-ui-impact-effort-matrix__legend-copy">
            <strong className="delpi-ui-impact-effort-matrix__legend-title">
              {quadrantLabels[item.key]}
            </strong>
            <span className="delpi-ui-impact-effort-matrix__legend-desc">
              {quadrantDescriptions[item.key]}
            </span>
          </span>
        </li>
      ))}
      {children}
    </ul>
  );
}
