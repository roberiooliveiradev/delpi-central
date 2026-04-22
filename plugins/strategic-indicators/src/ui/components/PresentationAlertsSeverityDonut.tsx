import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

type AlertSeverity = "high" | "medium" | "low";

type PresentationAlertsSeverityDonutProps = {
  values: {
    high: number;
    medium: number;
    low: number;
  };
};

type DonutDatum = {
  key: AlertSeverity;
  label: string;
  value: number;
};

type TooltipValue =
  | number
  | string
  | readonly (number | string)[]
  | undefined;

function getSeverityLabel(severity: AlertSeverity) {
  if (severity === "high") return "Alta";
  if (severity === "medium") return "Média";
  return "Baixa";
}

function getSeverityColorToken(severity: AlertSeverity) {
  if (severity === "high") return "var(--danger, #dc2626)";
  if (severity === "medium") return "var(--warning, #f59e0b)";
  return "var(--primary, #089bdb)";
}

function toTooltipNumber(value: TooltipValue): string {
  if (typeof value === "number" || typeof value === "string") {
    return String(value);
  }

  if (Array.isArray(value) && value.length > 0) {
    return String(value[0] ?? 0);
  }

  return "0";
}

export function PresentationAlertsSeverityDonut({
  values,
}: PresentationAlertsSeverityDonutProps) {
  const baseData: DonutDatum[] = [
    { key: "high", label: "Alta", value: values.high },
    { key: "medium", label: "Média", value: values.medium },
    { key: "low", label: "Baixa", value: values.low },
  ];

  const data = baseData.filter((item): item is DonutDatum => item.value > 0);

  const total = values.high + values.medium + values.low;

  return (
    <section className="si-presentation-alerts-donut si-presentation-scene-card">
      <div className="si-presentation-alerts-donut__header">
        <div>
          <span className="si-presentation-alerts-donut__eyebrow">
            Distribuição de severidade
          </span>
          <h3>Mapa executivo de alertas</h3>
        </div>

        <div className="si-presentation-alerts-donut__total">
          <strong>{total}</strong>
          <span>alertas totais</span>
        </div>
      </div>

      <div className="si-presentation-alerts-donut__content">
        <div className="si-presentation-alerts-donut__chart">
          {data.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={58}
                  outerRadius={84}
                  paddingAngle={3}
                  stroke="transparent"
                >
                  {data.map((entry) => (
                    <Cell
                      key={entry.key}
                      fill={getSeverityColorToken(entry.key)}
                    />
                  ))}
                </Pie>

                <Tooltip
                  formatter={(value, name) => [
                    toTooltipNumber(value),
                    String(name ?? ""),
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="si-presentation-alerts-donut__empty">
              Sem alertas para exibição.
            </div>
          )}
        </div>

        <div className="si-presentation-alerts-donut__legend">
          {(["high", "medium", "low"] as AlertSeverity[]).map((severity) => (
            <div
              key={severity}
              className="si-presentation-alerts-donut__legend-item"
            >
              <span
                className="si-presentation-alerts-donut__legend-dot"
                style={{
                  background: getSeverityColorToken(severity),
                }}
              />

              <div className="si-presentation-alerts-donut__legend-copy">
                <strong>{getSeverityLabel(severity)}</strong>
                <span>
                  {severity === "high"
                    ? values.high
                    : severity === "medium"
                    ? values.medium
                    : values.low}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}