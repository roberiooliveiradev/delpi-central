import type { CSSProperties } from "react";
import "./PresentationIgdGauge.css";

type PresentationIgdGaugeProps = {
  value: number;
  max?: number;
  classification?: string;
  variationLabel?: string;
  variationValue?: number;
  size?: number;
};

const GAUGE_SEGMENTS = [
  { label: "Crítico", from: 0, to: 4, color: "#ef4444" },
  { label: "Regular", from: 4, to: 6, color: "#f97316" },
  { label: "Satisfatório", from: 6, to: 8, color: "#eab308" },
  { label: "Alto Desempenho", from: 8, to: 9, color: "#84cc16" },
  { label: "Excelência", from: 9, to: 10, color: "#22c55e" },
] as const;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function toRadians(degrees: number) {
  return (degrees * Math.PI) / 180;
}

/**
 * Sistema angular:
 * - 180° = extremo esquerdo
 * - 90°  = topo
 * - 0°   = extremo direito
 */
function pointOnArc(
  centerX: number,
  centerY: number,
  radius: number,
  angleDeg: number,
) {
  const angle = toRadians(angleDeg);
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY - radius * Math.sin(angle),
  };
}

function describeArc(
  centerX: number,
  centerY: number,
  radius: number,
  startAngleDeg: number,
  endAngleDeg: number,
) {
  const start = pointOnArc(centerX, centerY, radius, startAngleDeg);
  const end = pointOnArc(centerX, centerY, radius, endAngleDeg);
  const largeArcFlag = Math.abs(endAngleDeg - startAngleDeg) > 180 ? 1 : 0;

  return [
    "M",
    start.x,
    start.y,
    "A",
    radius,
    radius,
    0,
    largeArcFlag,
    1,
    end.x,
    end.y,
  ].join(" ");
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function valueToAngle(value: number, max: number) {
  const normalized = clamp(value, 0, max) / max;
  return 180 - normalized * 180;
}

export function PresentationIgdGauge({
  value,
  max = 10,
  classification,
  variationLabel,
  variationValue,
  size = 360,
}: PresentationIgdGaugeProps) {
  const safeValue = clamp(value, 0, max);

  const strokeWidth = Math.max(18, Math.round(size * 0.06));
  const radius = size / 2 - strokeWidth;
  const centerX = size / 2;
  const centerY = size / 2;
  const svgHeight = size / 2 + strokeWidth + 20;

  const markerAngle = valueToAngle(safeValue, max);
  const marker = pointOnArc(centerX, centerY, radius, markerAngle);

  const summaryStyle = {
    "--si-gauge-marker-color":
      safeValue >= 9
        ? "#22c55e"
        : safeValue >= 8
          ? "#84cc16"
          : safeValue >= 6
            ? "#eab308"
            : safeValue >= 4
              ? "#f97316"
              : "#ef4444",
  } as CSSProperties;

  return (
    <section className="si-presentation-gauge" style={summaryStyle}>
      <div className="si-presentation-gauge__visual">
        <svg
          className="si-presentation-gauge__svg"
          width={size}
          height={svgHeight}
          viewBox={`0 0 ${size} ${svgHeight}`}
          role="img"
          aria-label={`IGD atual ${formatScore(safeValue)} de ${formatScore(max)}`}
        >
          {/* trilha base */}
          <path
            d={describeArc(centerX, centerY, radius, 180, 0)}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* segmentos */}
          {GAUGE_SEGMENTS.map((segment) => {
            const startAngle = valueToAngle(segment.from, max);
            const endAngle = valueToAngle(segment.to, max);

            return (
              <path
                key={segment.label}
                d={describeArc(centerX, centerY, radius, startAngle, endAngle)}
                fill="none"
                stroke={segment.color}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                opacity={0.95}
              />
            );
          })}

          {/* ponteiros/base escura laterais opcionais */}
          <path
            d={describeArc(centerX, centerY, radius, 180, 170)}
            fill="none"
            stroke="rgba(15,23,42,0.92)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          <path
            d={describeArc(centerX, centerY, radius, 10, 0)}
            fill="none"
            stroke="rgba(15,23,42,0.92)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* marcador */}
          <circle
            cx={marker.x}
            cy={marker.y}
            r={strokeWidth * 0.34}
            fill="var(--si-gauge-marker-color)"
            stroke="rgba(255,255,255,0.96)"
            strokeWidth={Math.max(3, strokeWidth * 0.14)}
          />
        </svg>

        <div className="si-presentation-gauge__center">
          <span className="si-presentation-gauge__label">IGD</span>
          <strong className="si-presentation-gauge__value">
            {formatScore(safeValue)}
          </strong>

          {classification ? (
            <span className="si-presentation-gauge__classification">
              {classification}
            </span>
          ) : null}

          {variationLabel ? (
            <span className="si-presentation-gauge__variation">
              {variationValue !== undefined
                ? `${variationValue > 0 ? "+" : ""}${formatScore(variationValue)} · `
                : ""}
              {variationLabel}
            </span>
          ) : null}
        </div>
      </div>
    </section>
  );
}