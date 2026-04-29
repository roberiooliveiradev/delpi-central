import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DepartmentTrendItem } from "../../data/types/trends";
import { StatusBadge } from "./StatusBadge";
import "./DepartmentTrendGrid.css";

type DepartmentTrendGridProps = {
  departments: DepartmentTrendItem[];
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
      const parsed = Number(item);
      if (Number.isFinite(parsed)) return parsed;
    }
  }

  return 0;
}

function formatScore(value: number | TooltipValue) {
  return toNumber(value as TooltipValue).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
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

function getDirectionLabel(direction: DepartmentTrendItem["direction"]) {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getDirectionVariant(
  direction: DepartmentTrendItem["direction"],
): "success" | "warning" | "neutral" {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

function getDirectionClassName(direction: DepartmentTrendItem["direction"]) {
  if (direction === "up") return "si-department-trend-card--up";
  if (direction === "down") return "si-department-trend-card--down";
  return "si-department-trend-card--stable";
}

function resolveTrendColor(direction: DepartmentTrendItem["direction"]) {
  if (direction === "up") return "#22c55e";
  if (direction === "down") return "#ef4444";
  return "#3b82f6";
}

function buildSeries(department: DepartmentTrendItem) {
  if (department.series?.length) {
    return department.series.map((point) => ({
      period: point.period,
      score: point.score,
    }));
  }

  return [
    {
      period: "Anterior",
      score: department.previous,
    },
    {
      period: "Atual",
      score: department.current,
    },
  ];
}

export function DepartmentTrendGrid({ departments }: DepartmentTrendGridProps) {
  if (!departments.length) {
    return (
      <div className="si-department-trend-grid si-department-trend-grid--empty">
        Nenhum departamento encontrado no recorte temporal atual.
      </div>
    );
  }

  return (
    <div className="si-department-trend-grid">
      {departments.map((department) => {
        const delta = department.current - department.previous;
        const chartData = buildSeries(department);
        const gradientId = `department-trend-${department.id}`;
        const chartColor = resolveTrendColor(department.direction);

        return (
          <article
            key={department.id}
            className={`si-department-trend-card ${getDirectionClassName(
              department.direction,
            )}`}
          >
            <div className="si-department-trend-card__top">
              <div>
                <h3 className="si-department-trend-card__title">
                  {department.name}
                </h3>

                <p className="si-department-trend-card__subtitle">
                  {department.currentClassification ?? "Leitura temporal"}
                </p>
              </div>

              <StatusBadge
                label={getDirectionLabel(department.direction)}
                variant={getDirectionVariant(department.direction)}
              />
            </div>

            <div className="si-department-trend-card__sparkline">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={chartData}
                  margin={{ top: 6, right: 0, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient
                      id={gradientId}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor={chartColor}
                        stopOpacity={0.34}
                      />
                      <stop
                        offset="100%"
                        stopColor={chartColor}
                        stopOpacity={0.03}
                      />
                    </linearGradient>
                  </defs>

                  <XAxis dataKey="period" hide />
                  <YAxis hide domain={["dataMin - 0.5", "dataMax + 0.5"]} />

                  <Tooltip
                    formatter={(value) => [formatScore(value), "Score"]}
                    labelFormatter={(label) => `Competência ${label}`}
                    cursor={false}
                    contentStyle={{
                      borderRadius: 12,
                      border: "1px solid rgba(255,255,255,0.12)",
                      background: "rgba(15, 23, 42, 0.96)",
                      color: "#ffffff",
                      boxShadow: "0 18px 40px rgba(0,0,0,0.28)",
                    }}
                  />

                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke={chartColor}
                    strokeWidth={3}
                    fill={`url(#${gradientId})`}
                    dot={{
                      r: 3,
                      fill: chartColor,
                      stroke: "var(--surface, #ffffff)",
                      strokeWidth: 1.5,
                    }}
                    activeDot={{
                      r: 5,
                      fill: chartColor,
                      stroke: "var(--surface, #ffffff)",
                      strokeWidth: 2,
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="si-department-trend-card__metrics">
              <div className="si-department-trend-card__metric">
                <span>Atual</span>
                <strong>{formatScore(department.current)}</strong>
              </div>

              <div className="si-department-trend-card__metric">
                <span>Anterior</span>
                <strong>{formatScore(department.previous)}</strong>
              </div>

              <div className="si-department-trend-card__metric">
                <span>Variação</span>
                <strong>{formatVariation(delta)}</strong>
              </div>
            </div>

            <div className="si-department-trend-card__footer">
              <span>Melhor: {formatScore(department.bestScore)}</span>
              <span>Pior: {formatScore(department.worstScore)}</span>
            </div>
          </article>
        );
      })}
    </div>
  );
}