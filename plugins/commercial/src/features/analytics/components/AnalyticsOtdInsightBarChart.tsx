import { useId, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAvatar } from "../../customers/components/CustomerAvatar";
import type { OtdCustomerIdentity } from "./OtdCustomerIdentityCell";

export type OtdInsightBarRow = {
  id: string;
  value: number;
  customer: OtdCustomerIdentity;
  /** Rótulo no eixo Y (ex.: pedido); default = nome do cliente. */
  axisLabel?: string;
};

type AnalyticsOtdInsightBarChartProps = {
  rows: OtdInsightBarRow[];
  valueLabel: string;
  formatValue?: (value: number) => string;
  emptyMessage: string;
  onRowClick?: (row: OtdInsightBarRow) => void;
};

type ChartDatum = OtdInsightBarRow & {
  label: string;
  codeStore: string;
  displayName: string;
};

const COLOR_DANGER = "var(--cm-danger, #dc2626)";
const COLOR_WARNING = "var(--cm-warning, #d97706)";
const COLOR_SUCCESS = "var(--cm-success, #16a34a)";

function alertFill(value: number, max: number): string {
  if (max <= 0) return COLOR_SUCCESS;
  const ratio = value / max;
  if (ratio >= 0.75) return COLOR_DANGER;
  if (ratio >= 0.4) return COLOR_WARNING;
  return COLOR_SUCCESS;
}

function InsightTooltip({
  active,
  payload,
  valueLabel,
  formatValue,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDatum }>;
  valueLabel: string;
  formatValue: (value: number) => string;
}) {
  if (!active || !payload?.[0]) return null;
  const row = payload[0].payload;
  return (
    <div className="cm-otd-insight-tooltip">
      <div className="cm-open-orders-client">
        {row.customer.code ? (
          <CustomerAvatar
            code={row.customer.code}
            store={(row.customer.store ?? "").trim() || "01"}
            name={row.displayName}
            hasAvatar={Boolean(row.customer.hasAvatar)}
            size="sm"
            previewable={false}
          />
        ) : null}
        <div className="cm-open-orders-client__text">
          {row.axisLabel ? (
            <span className="cm-otd-customer-eyebrow">{row.axisLabel}</span>
          ) : null}
          <strong className="cm-open-orders-client__name">{row.displayName}</strong>
          <span className="cm-open-orders-client__id">{row.codeStore}</span>
        </div>
      </div>
      <p className="cm-otd-insight-tooltip__value">
        {valueLabel}: {formatValue(row.value)}
      </p>
    </div>
  );
}

/**
 * Barras horizontais recharts (mesmo pacote do ROL) + tokens `cm` (claro/escuro).
 * Eixo Y com avatar/nome/loja via foreignObject.
 */
export function AnalyticsOtdInsightBarChart({
  rows,
  valueLabel,
  formatValue = (v) => v.toLocaleString("pt-BR"),
  emptyMessage,
  onRowClick,
}: AnalyticsOtdInsightBarChartProps) {
  const gid = useId().replace(/:/g, "");
  const max = useMemo(
    () => Math.max(0, ...rows.map((row) => Number(row.value) || 0)),
    [rows],
  );
  const data: ChartDatum[] = useMemo(
    () =>
      rows.map((row) => {
        const code = (row.customer.code ?? "").trim();
        const store = (row.customer.store ?? "").trim() || "01";
        const displayName =
          (row.customer.name ?? "").trim() ||
          (row.customer.shortName ?? "").trim() ||
          code ||
          "—";
        const codeStore =
          code && store
            ? formatEntityCodeStore(code, store) ?? `${code} · Loja ${store}`
            : code || "—";
        return {
          ...row,
          label: row.id,
          displayName,
          codeStore,
        };
      }),
    [rows],
  );
  const height = Math.max(220, data.length * 58 + 40);

  if (data.length === 0) {
    return <p className="cm-muted">{emptyMessage}</p>;
  }

  return (
    <div className="cm-chart-wrap cm-otd-insight-chart" style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 8, right: 20, left: 4, bottom: 8 }}
          barCategoryGap="22%"
          onClick={(state) => {
            const payload = (
              state as { activePayload?: Array<{ payload?: ChartDatum }> } | null
            )?.activePayload?.[0]?.payload;
            if (!payload?.id || !onRowClick) return;
            const row = rows.find((item) => item.id === payload.id);
            if (row) onRowClick(row);
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--cm-border)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: "var(--cm-muted)", fontSize: 11 }}
            stroke="var(--cm-border)"
          />
          <YAxis
            type="category"
            dataKey="label"
            width={168}
            interval={0}
            tick={(props) => {
              const { x, y, payload } = props;
              const row = data.find((item) => item.label === payload.value);
              if (!row) return <g />;
              const store = (row.customer.store ?? "").trim() || "01";
              const code = (row.customer.code ?? "").trim();
              return (
                <g transform={`translate(${x},${y})`}>
                  <foreignObject x={-164} y={-22} width={160} height={44}>
                    <div className="cm-otd-insight-chart__tick">
                      {code ? (
                        <CustomerAvatar
                          code={code}
                          store={store}
                          name={row.displayName}
                          hasAvatar={Boolean(row.customer.hasAvatar)}
                          size="sm"
                          previewable={false}
                        />
                      ) : null}
                      <div className="cm-otd-insight-chart__tick-text">
                        {row.axisLabel ? (
                          <span className="cm-otd-customer-eyebrow">{row.axisLabel}</span>
                        ) : null}
                        <strong>{row.displayName}</strong>
                        <span>{row.codeStore}</span>
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            }}
            stroke="var(--cm-border)"
          />
          <Tooltip
            cursor={{ fill: "color-mix(in srgb, var(--cm-accent) 12%, transparent)" }}
            content={
              <InsightTooltip valueLabel={valueLabel} formatValue={formatValue} />
            }
          />
          <Bar
            dataKey="value"
            name={valueLabel}
            radius={[0, 6, 6, 0]}
            maxBarSize={22}
            cursor={onRowClick ? "pointer" : "default"}
          >
            {data.map((row) => (
              <Cell
                key={`${gid}-${row.id}`}
                fill={alertFill(Number(row.value) || 0, max)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
