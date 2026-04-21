import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

type PresentationAlertsSeverityDonutProps = {
  high: number;
  medium: number;
  low: number;
};

type TooltipValue =
  | number
  | string
  | readonly (string | number)[]
  | undefined;

const SEVERITY_DATA = [
  { key: "high", label: "Alta", color: "#ef4444" },
  { key: "medium", label: "Média", color: "#f59e0b" },
  { key: "low", label: "Baixa", color: "#22c55e" },
] as const;

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

export function PresentationAlertsSeverityDonut({
  high,
  medium,
  low,
}: PresentationAlertsSeverityDonutProps) {
  const chartData = [
    { name: "Alta", value: high, color: "#ef4444" },
    { name: "Média", value: medium, color: "#f59e0b" },
    { name: "Baixa", value: low, color: "#22c55e" },
  ].filter((item) => item.value > 0);

  const total = high + medium + low;

  return (
    <section className="si-presentation-alerts-donut">
      <div className="si-presentation-alerts-donut__chart">
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip
                formatter={(value, name) => [toNumber(value), String(name)]}
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.12)",
                  background: "rgba(15, 23, 42, 0.96)",
                  color: "#ffffff",
                }}
              />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius="62%"
                outerRadius="100%"
                paddingAngle={4}
                stroke="transparent"
              >
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="si-presentation-alerts-donut__empty">
            Sem alertas
          </div>
        )}

        <div className="si-presentation-alerts-donut__center">
          <span className="si-presentation-alerts-donut__label">Alertas</span>
          <strong className="si-presentation-alerts-donut__value">
            {total}
          </strong>
        </div>
      </div>

      <div className="si-presentation-alerts-donut__legend">
        {SEVERITY_DATA.map((item) => {
          const value =
            item.key === "high" ? high : item.key === "medium" ? medium : low;

          return (
            <div
              key={item.key}
              className="si-presentation-alerts-donut__legend-item"
            >
              <span
                className="si-presentation-alerts-donut__legend-dot"
                style={{ background: item.color }}
              />
              <span className="si-presentation-alerts-donut__legend-label">
                {item.label}
              </span>
              <strong className="si-presentation-alerts-donut__legend-value">
                {value}
              </strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}