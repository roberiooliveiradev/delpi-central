import { formatNumber, formatPct } from "./nativeFormat";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
    return formatNumber(value);
  }
  return String(value);
}

export function TvDataLineChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = resolved.chart?.points ?? [];
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value ?? 0));
  const max = Math.max(...values, 1);
  const width = 100;
  const height = 60;
  const step = points.length > 1 ? width / (points.length - 1) : width;
  const coords = points.map((point, index) => {
    const x = index * step;
    const y = height - (Number(point.value ?? 0) / max) * height;
    return `${x},${y}`;
  });
  return (
    <div className="tdp-data-chart">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="none">
        <polyline points={coords.join(" ")} fill="none" stroke="#38bdf8" strokeWidth="2" />
      </svg>
    </div>
  );
}

export function TvDataBarChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = resolved.chart?.points ?? [];
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value ?? 0));
  const max = Math.max(...values, 1);
  const width = 100;
  const height = 60;
  const barWidth = width / Math.max(points.length, 1);
  const gap = Math.min(barWidth * 0.15, 2);
  const effectiveBarWidth = Math.max(barWidth - gap, 1);

  return (
    <div className="tdp-data-chart tdp-data-chart--bar">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="none">
        {points.map((point, index) => {
          const value = Number(point.value ?? 0);
          const barHeight = (value / max) * height;
          const x = index * barWidth + gap / 2;
          const y = height - barHeight;
          return (
            <rect
              key={`bar-${index}`}
              x={x}
              y={y}
              width={effectiveBarWidth}
              height={barHeight}
              fill="#38bdf8"
              rx="0.5"
            />
          );
        })}
      </svg>
    </div>
  );
}

export function TvDataKpiWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const label = resolved.kpi?.label ?? resolved.label ?? "Dados";
  const value = formatCellValue(resolved.kpi?.value);
  return (
    <div className="tdp-data-kpi">
      <span className="tdp-data-kpi__label">{label}</span>
      <strong className="tdp-data-kpi__value">{value}</strong>
    </div>
  );
}
