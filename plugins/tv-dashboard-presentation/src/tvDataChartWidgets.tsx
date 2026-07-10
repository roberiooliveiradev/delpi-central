import { formatNumber, formatPct } from "./nativeFormat";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

type ChartPoint = { label?: unknown; value?: unknown };

export function usableChartPoints(points: ChartPoint[]): ChartPoint[] {
  return points.filter((point) => {
    const raw = point.value;
    if (raw === null || raw === undefined || raw === "") return false;
    return Number.isFinite(Number(raw));
  });
}

export function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Math.abs(value) <= 100 && !Number.isInteger(value)) return formatPct(value);
    return formatNumber(value);
  }
  return String(value);
}

export function TvDataLineChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = usableChartPoints(resolved.chart?.points ?? []);
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1e-6);
  const width = 100;
  const height = 60;
  const padX = 4;
  const padY = 6;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const step = points.length > 1 ? innerW / (points.length - 1) : 0;
  const coords = points.map((point, index) => {
    const x = padX + index * step;
    const normalized = (Number(point.value) - min) / range;
    const y = padY + innerH - normalized * innerH;
    return `${x},${y}`;
  });
  return (
    <div className="tdp-data-chart">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="xMidYMid meet">
        <polyline
          points={coords.join(" ")}
          fill="none"
          stroke="var(--tdp-data-accent, #38bdf8)"
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

export function TvDataBarChartWidget({ resolved }: { resolved: ComunicadoDataResolved }) {
  const points = usableChartPoints(resolved.chart?.points ?? []);
  if (points.length === 0) {
    return <div className="tdp-data-chart tdp-data-chart--empty">Sem série</div>;
  }
  const values = points.map((point) => Number(point.value));
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  const range = Math.max(max - min, 1e-6);
  const width = 100;
  const height = 60;
  const padX = 4;
  const padY = 6;
  const innerW = width - padX * 2;
  const innerH = height - padY * 2;
  const barWidth = innerW / Math.max(points.length, 1);
  const gap = Math.min(barWidth * 0.18, 2.5);
  const effectiveBarWidth = Math.max(barWidth - gap, 1);

  return (
    <div className="tdp-data-chart tdp-data-chart--bar">
      <svg viewBox={`0 0 ${width} ${height}`} className="tdp-data-chart__svg" preserveAspectRatio="xMidYMid meet">
        {points.map((point, index) => {
          const value = Number(point.value);
          const normalized = (value - min) / range;
          const barHeight = normalized * innerH;
          const x = padX + index * barWidth + gap / 2;
          const y = padY + innerH - barHeight;
          return (
            <rect
              key={`bar-${index}`}
              x={x}
              y={y}
              width={effectiveBarWidth}
              height={barHeight}
              fill="var(--tdp-data-accent, #38bdf8)"
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
