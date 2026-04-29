import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IgdTrendPoint } from "../../data/types/trends";
import { StatusBadge } from "./StatusBadge";
import "./IgdTrendTimeline.css";

type IgdTrendTimelineProps = {
  series: IgdTrendPoint[];
};

type TooltipValue =
  | number
  | string
  | readonly (string | number)[]
  | undefined;

function toNumber(value: TooltipValue): number {
  if (typeof value === "number") return value;

  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      if (typeof item === "number" && Number.isFinite(item)) {
        return item;
      }

      if (typeof item === "string") {
        const parsed = Number(item);
        if (Number.isFinite(parsed)) {
          return parsed;
        }
      }
    }
  }

  return 0;
}

function formatScore(value: TooltipValue) {
  return toNumber(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function getVariationLabel(value: number) {
  if (value > 0.09) return "Melhora";
  if (value < -0.09) return "Queda";
  return "Estável";
}

function getVariationVariant(value: number): "success" | "warning" | "neutral" {
  if (value > 0.09) return "success";
  if (value < -0.09) return "warning";
  return "neutral";
}

function formatVariation(value: number) {
  const formatted = Math.abs(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return "0,0";
}

export function IgdTrendTimeline({ series }: IgdTrendTimelineProps) {
  const currentPoint = series[series.length - 1] ?? null;
  const previousPoint = series[series.length - 2] ?? null;

  const variation =
    currentPoint && previousPoint ? currentPoint.value - previousPoint.value : 0;

  const bestPoint = series.reduce<IgdTrendPoint | null>((best, point) => {
    if (!best || point.value > best.value) return point;
    return best;
  }, null);

  const worstPoint = series.reduce<IgdTrendPoint | null>((worst, point) => {
    if (!worst || point.value < worst.value) return point;
    return worst;
  }, null);

  const points = series.map((point) => ({
    period: point.period,
    value: point.value,
    classification: point.classification,
  }));

  if (!points.length) {
    return (
      <section className="si-igd-timeline si-igd-timeline--empty">
        Nenhuma série histórica encontrada para o recorte atual.
      </section>
    );
  }

  return (
    <section className="si-igd-timeline">
      <div className="si-igd-timeline__header">
        <div>
          <p className="si-igd-timeline__eyebrow">Evolução mensal</p>
          <h3 className="si-igd-timeline__title">Linha temporal do IGD</h3>
          <p className="si-igd-timeline__subtitle">
            Série histórica real do índice global no intervalo solicitado.
          </p>
        </div>

        <StatusBadge
          label={`${getVariationLabel(variation)} ${formatVariation(variation)}`}
          variant={getVariationVariant(variation)}
        />
      </div>

      <div className="si-igd-timeline__chart-shell">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={points}
            margin={{ top: 16, right: 18, left: -8, bottom: 2 }}
          >
            <defs>
              <linearGradient
                id="si-igd-trend-area"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor="#089bdb" stopOpacity={0.5} />
                <stop offset="48%" stopColor="#089bdb" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#089bdb" stopOpacity={0.03} />
              </linearGradient>

              <linearGradient
                id="si-igd-trend-stroke"
                x1="0"
                y1="0"
                x2="1"
                y2="0"
              >
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="52%" stopColor="#089bdb" />
                <stop offset="100%" stopColor="#22c55e" />
              </linearGradient>
            </defs>

            <CartesianGrid
              vertical={false}
              stroke="color-mix(in srgb, var(--si-card-border) 76%, transparent)"
              strokeDasharray="4 4"
            />

            <XAxis
              dataKey="period"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--si-text-muted)", fontSize: 12 }}
            />

            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--si-text-muted)", fontSize: 12 }}
              domain={["dataMin - 0.5", "dataMax + 0.5"]}
              tickFormatter={(value) => formatScore(value)}
            />

            <ReferenceLine
              y={7}
              stroke="rgba(245, 183, 0, 0.68)"
              strokeDasharray="5 5"
              label={{
                value: "Atenção",
                fill: "var(--si-text-muted)",
                fontSize: 11,
                position: "insideTopRight",
              }}
            />

            <ReferenceLine
              y={8}
              stroke="rgba(8, 155, 219, 0.62)"
              strokeDasharray="5 5"
              label={{
                value: "Alto desempenho",
                fill: "var(--si-text-muted)",
                fontSize: 11,
                position: "insideTopRight",
              }}
            />

            <Tooltip
              formatter={(value) => [formatScore(value), "IGD"]}
              labelFormatter={(label) => `Competência ${label}`}
              contentStyle={{
                borderRadius: 14,
                border: "1px solid rgba(255,255,255,0.12)",
                background: "rgba(15, 23, 42, 0.96)",
                color: "#ffffff",
                boxShadow: "0 18px 40px rgba(0,0,0,0.28)",
              }}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke="url(#si-igd-trend-stroke)"
              strokeWidth={4}
              fill="url(#si-igd-trend-area)"
              dot={{
                r: 5,
                fill: "#089bdb",
                stroke: "#ffffff",
                strokeWidth: 2,
              }}
              activeDot={{
                r: 7,
                fill: "#089bdb",
                stroke: "#ffffff",
                strokeWidth: 2,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="si-igd-timeline__summary">
        <div className="si-igd-timeline__summary-card">
          <span>Atual</span>
          <strong>{currentPoint ? formatScore(currentPoint.value) : "0,0"}</strong>
          <small>{currentPoint?.period ?? "Sem período"}</small>
        </div>

        <div className="si-igd-timeline__summary-card">
          <span>Melhor ponto</span>
          <strong>{bestPoint ? formatScore(bestPoint.value) : "0,0"}</strong>
          <small>{bestPoint?.period ?? "Sem período"}</small>
        </div>

        <div className="si-igd-timeline__summary-card">
          <span>Pior ponto</span>
          <strong>{worstPoint ? formatScore(worstPoint.value) : "0,0"}</strong>
          <small>{worstPoint?.period ?? "Sem período"}</small>
        </div>

        <div className="si-igd-timeline__summary-card">
          <span>Variação</span>
          <strong>{formatVariation(variation)}</strong>
          <small>{getVariationLabel(variation)}</small>
        </div>
      </div>
    </section>
  );
}