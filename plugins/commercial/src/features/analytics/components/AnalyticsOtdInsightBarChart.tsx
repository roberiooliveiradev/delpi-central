import { useId, useMemo } from "react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  RANKING_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
} from "@delpi/plugin-ui/index";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CommercialTabularExportButtons } from "../../../app/commercialUi";

import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAvatar } from "../../customers/components/CustomerAvatar";
import {
  buildCustomerDetailHref,
  navigatePluginPath,
} from "../../../app/pluginNavigation";
import { currentReturnNav } from "../../../app/commercialNavigationReturn";
import { accountLinkTitle } from "../../../content/entityLinkHints";
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
  fill: string;
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

function customerAccountHref(code: string, store: string): string | null {
  return buildCustomerDetailHref(code, store, {
    search: "",
    returnNav: currentReturnNav("OTD"),
  });
}

function InsightCustomerAvatar({ row }: { row: ChartDatum }) {
  const code = (row.customer.code ?? "").trim();
  const store = (row.customer.store ?? "").trim() || "01";
  if (!code) return null;
  const href = customerAccountHref(code, store);
  const title = accountLinkTitle(row.displayName);
  if (href) {
    return (
      <CustomerAvatar
        code={code}
        store={store}
        name={row.displayName}
        hasAvatar={Boolean(row.customer.hasAvatar)}
        size="sm"
        href={href}
        title={title}
        onNavigate={() => navigatePluginPath(href)}
      />
    );
  }
  return (
    <CustomerAvatar
      code={code}
      store={store}
      name={row.displayName}
      hasAvatar={Boolean(row.customer.hasAvatar)}
      size="sm"
      previewable={false}
    />
  );
}

function InsightTickContent({
  row,
  compact = false,
}: {
  row: ChartDatum;
  compact?: boolean;
}) {
  return (
    <div
      className={
        compact
          ? "cm-otd-insight-chart__tick cm-otd-insight-chart__tick--compact"
          : "cm-otd-insight-chart__tick"
      }
    >
      <InsightCustomerAvatar row={row} />
      <div className="cm-otd-insight-chart__tick-text">
        {row.axisLabel ? (
          <span className="cm-otd-customer-eyebrow">{row.axisLabel}</span>
        ) : null}
        <strong>{row.displayName}</strong>
        {compact ? null : <span>{row.codeStore}</span>}
      </div>
    </div>
  );
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
        <InsightCustomerAvatar row={row} />
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

function InsightPieLegend({
  data,
  formatValue,
}: {
  data: ChartDatum[];
  formatValue: (value: number) => string;
}) {
  return (
    <ul className="cm-otd-insight-chart__legend">
      {data.map((row) => (
        <li key={row.id} className="cm-otd-insight-chart__legend-item">
          <span
            className="cm-otd-insight-chart__legend-swatch"
            style={{ background: row.fill }}
            aria-hidden
          />
          <InsightCustomerAvatar row={row} />
          <div className="cm-otd-insight-chart__tick-text">
            {row.axisLabel ? (
              <span className="cm-otd-customer-eyebrow">{row.axisLabel}</span>
            ) : null}
            <strong>{row.displayName}</strong>
            <span>
              {row.codeStore} · {formatValue(row.value)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}

/**
 * Ranking OTD (reincidência / atrasos): Horiz. / Barras / Pizza com as mesmas
 * cores por severidade e avatares de cliente em todos os modos.
 */
export function AnalyticsOtdInsightBarChart({
  rows,
  valueLabel,
  formatValue = (v) => v.toLocaleString("pt-BR"),
  emptyMessage,
  onRowClick,
}: AnalyticsOtdInsightBarChartProps) {
  const gid = useId().replace(/:/g, "");
  const { preferences, setChartType } = usePersistedChartPreferences({
    storageKey: `commercial:otd-insight:${valueLabel}`,
    defaults: { chartType: "horizontal_bar" },
    allowedChartTypes: RANKING_TYPES,
  });
  const chartType = preferences.chartType ?? "horizontal_bar";
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
        const value = Number(row.value) || 0;
        return {
          ...row,
          label: row.id,
          displayName,
          codeStore,
          fill: alertFill(value, max),
        };
      }),
    [max, rows],
  );
  const horizontalHeight = Math.max(220, data.length * 58 + 40);
  const verticalHeight = Math.max(280, 220 + Math.min(data.length, 8) * 8);
  const pieHeight = Math.max(300, 180 + data.length * 36);

  if (data.length === 0) {
    return <p className="cm-muted">{emptyMessage}</p>;
  }

  const exportPayload = {
    title: valueLabel,
    columns: [
      { key: "cliente", label: "Cliente" },
      { key: "codigo", label: "Código/loja" },
      { key: "valor", label: valueLabel },
    ],
    rows: data.map((row) => ({
      cliente: row.displayName,
      codigo: row.codeStore,
      valor: formatValue(row.value),
    })),
  };

  const handlePlotClick = (state: unknown) => {
    const payload = (
      state as { activePayload?: Array<{ payload?: ChartDatum }> } | null
    )?.activePayload?.[0]?.payload;
    if (!payload?.id || !onRowClick) return;
    const row = rows.find((item) => item.id === payload.id);
    if (row) onRowClick(row);
  };

  return (
    <ChartViewShell
      prefix="cm"
      typeToggle={
        <ChartTypeSegmentToggle
          family="ranking"
          value={chartType}
          onChange={setChartType}
          categoryCount={data.length}
          idPrefix={`otd-insight-${gid}`}
          prefix="cm"
        />
      }
      exportActions={
        <CommercialTabularExportButtons
          compact
          onExport={(format) => {
            runTabularExport({ kind: "table", format, payload: exportPayload });
          }}
        />
      }
    >
      {chartType === "horizontal_bar" ? (
        <div
          className="cm-chart-wrap cm-otd-insight-chart"
          style={{ width: "100%", height: horizontalHeight }}
        >
          <ResponsiveContainer>
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 8, right: 20, left: 4, bottom: 8 }}
              barCategoryGap="22%"
              onClick={handlePlotClick}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--cm-border)"
                horizontal={false}
              />
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
                  return (
                    <g transform={`translate(${x},${y})`}>
                      <foreignObject x={-164} y={-22} width={160} height={44}>
                        <InsightTickContent row={row} />
                      </foreignObject>
                    </g>
                  );
                }}
                stroke="var(--cm-border)"
              />
              <Tooltip
                cursor={{
                  fill: "color-mix(in srgb, var(--cm-accent) 12%, transparent)",
                }}
                content={
                  <InsightTooltip
                    valueLabel={valueLabel}
                    formatValue={formatValue}
                  />
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
                  <Cell key={`${gid}-${row.id}`} fill={row.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {chartType === "bar" ? (
        <div
          className="cm-chart-wrap cm-otd-insight-chart cm-otd-insight-chart--vertical"
          style={{ width: "100%", height: verticalHeight }}
        >
          <ResponsiveContainer>
            <BarChart
              data={data}
              margin={{ top: 8, right: 12, left: 4, bottom: 8 }}
              barCategoryGap="18%"
              onClick={handlePlotClick}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--cm-border)"
                vertical={false}
              />
              <XAxis
                type="category"
                dataKey="label"
                interval={0}
                height={72}
                tick={(props) => {
                  const { x, y, payload } = props;
                  const row = data.find((item) => item.label === payload.value);
                  if (!row) return <g />;
                  return (
                    <g transform={`translate(${x},${y})`}>
                      <foreignObject x={-36} y={0} width={72} height={68}>
                        <InsightTickContent row={row} compact />
                      </foreignObject>
                    </g>
                  );
                }}
                stroke="var(--cm-border)"
              />
              <YAxis
                type="number"
                tick={{ fill: "var(--cm-muted)", fontSize: 11 }}
                stroke="var(--cm-border)"
                tickFormatter={(value) => formatValue(Number(value))}
              />
              <Tooltip
                cursor={{
                  fill: "color-mix(in srgb, var(--cm-accent) 12%, transparent)",
                }}
                content={
                  <InsightTooltip
                    valueLabel={valueLabel}
                    formatValue={formatValue}
                  />
                }
              />
              <Bar
                dataKey="value"
                name={valueLabel}
                radius={[6, 6, 0, 0]}
                maxBarSize={36}
                cursor={onRowClick ? "pointer" : "default"}
              >
                {data.map((row) => (
                  <Cell key={`${gid}-v-${row.id}`} fill={row.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {chartType === "pie" ? (
        <div
          className="cm-chart-wrap cm-otd-insight-chart cm-otd-insight-chart--pie"
          style={{ width: "100%", minHeight: pieHeight }}
        >
          <ResponsiveContainer width="100%" height={Math.max(220, pieHeight * 0.55)}>
            <PieChart>
              <Tooltip
                content={
                  <InsightTooltip
                    valueLabel={valueLabel}
                    formatValue={formatValue}
                  />
                }
              />
              <Pie
                data={data}
                dataKey="value"
                nameKey="displayName"
                cx="50%"
                cy="50%"
                outerRadius="72%"
                cursor={onRowClick ? "pointer" : "default"}
                onClick={(entry) => {
                  const payload = (entry as { payload?: ChartDatum } | null)
                    ?.payload;
                  if (!payload?.id || !onRowClick) return;
                  const row = rows.find((item) => item.id === payload.id);
                  if (row) onRowClick(row);
                }}
              >
                {data.map((row) => (
                  <Cell key={`${gid}-p-${row.id}`} fill={row.fill} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <InsightPieLegend data={data} formatValue={formatValue} />
        </div>
      ) : null}
    </ChartViewShell>
  );
}
