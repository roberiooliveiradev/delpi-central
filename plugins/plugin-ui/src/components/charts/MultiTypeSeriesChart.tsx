import { useMemo } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  LabelList,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { PersistedChartType } from "../../hooks/usePersistedChartPreferences";
import { withLinearTrendField } from "../../utils/linearTrendSeries";
import { StableResponsiveContainer } from "./StableResponsiveContainer";

export type MultiTypeSeriesSpec = {
  dataKey: string;
  name: string;
  fill: string;
  /** OLS trend source (column/line/area only). */
  trendSource?: boolean;
};

export type MultiTypeSeriesChartProps = {
  data: ReadonlyArray<Record<string, unknown>>;
  categoryKey: string;
  series: ReadonlyArray<MultiTypeSeriesSpec>;
  chartType: PersistedChartType;
  height?: number;
  showTrend?: boolean;
  trendSeriesName?: string;
  formatY?: (value: number) => string;
  formatTooltipValue?: (value: number) => string;
  showLegend?: boolean;
  /**
   * Rótulo de valor nas barras/colunas (acima da coluna, à direita da barra).
   * Default false — não altera dashboards existentes.
   */
  showValueLabels?: boolean;
  onCategoryClick?: (category: string) => void;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  /**
   * When set (ranking charts), each category reads its fill from this data key
   * instead of a single series color (pie / bar / horizontal_bar / column).
   */
  categoryFillKey?: string;
};

/** Traço/espessura diferenciam tendência da série; a cor herda de `series.fill`. */
const TREND_STROKE_WIDTH = 3;
const TREND_DASH = "8 5";

function defaultFormatY(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function resolveCategoryFill(
  row: Record<string, unknown>,
  categoryFillKey: string | undefined,
  fallback: string,
): string {
  if (!categoryFillKey) return fallback;
  const raw = row[categoryFillKey];
  return typeof raw === "string" && raw.trim() ? raw : fallback;
}

const VALUE_LABEL_STYLE = {
  fill: "var(--delpi-ui-text, #0f172a)",
  fontSize: 11,
  fontWeight: 600,
} as const;

/** Rótulo de valor nas barras — posição depende da orientação. */
function barValueLabels(
  show: boolean,
  format: (value: number) => string,
  position: "top" | "right",
) {
  if (!show) return null;
  return (
    <LabelList
      position={position}
      formatter={(value: unknown) =>
        value == null || Number.isNaN(Number(value)) ? "" : format(Number(value))
      }
      style={VALUE_LABEL_STYLE}
    />
  );
}

/**
 * Recharts multi-type series plot (column / line / area / pie / bar / horizontal / stacked).
 */
export function MultiTypeSeriesChart({
  data,
  categoryKey,
  series,
  chartType,
  height = 280,
  showTrend = false,
  trendSeriesName = "Tendência",
  formatY = defaultFormatY,
  formatTooltipValue,
  showLegend = true,
  showValueLabels = false,
  onCategoryClick,
  margin = { top: 12, right: 16, left: 4, bottom: 4 },
  categoryFillKey,
}: MultiTypeSeriesChartProps) {
  const trendSources = useMemo(
    () => series.filter((entry) => entry.trendSource),
    [series],
  );

  /**
   * Recharts 3 guarda Bar no store na ordem de 1ª inscrição. Trocar a ordem
   * do array `series` sem remontar deixa as colunas no offset antigo (ex.:
   * Dia→Mês YoY: `produced` fica à esquerda e o ano anterior à direita).
   */
  const seriesOrderKey = useMemo(
    () => series.map((entry) => entry.dataKey).join("|"),
    [series],
  );

  const chartData = useMemo(() => {
    let rows = data.map((row) => ({ ...row }));
    const trendAllowed =
      chartType === "column" || chartType === "line" || chartType === "area";
    if (!showTrend || !trendAllowed || trendSources.length === 0) return rows;
    for (const source of trendSources) {
      rows = withLinearTrendField(rows, source.dataKey, `_trend_${source.dataKey}`);
    }
    return rows;
  }, [chartType, data, showTrend, trendSources]);

  const tooltipValue = formatTooltipValue ?? formatY;

  const formatTooltip = (value: unknown, name: unknown): [string, string] => [
    value == null || Number.isNaN(Number(value)) ? "—" : tooltipValue(Number(value)),
    String(name ?? ""),
  ];

  const handleBarCategoryClick = (bar: unknown) => {
    if (!onCategoryClick) return;
    const payload = (bar as { payload?: Record<string, unknown> } | null)?.payload;
    const category = payload?.[categoryKey];
    if (category != null) onCategoryClick(String(category));
  };

  const trendLines =
    showTrend &&
    (chartType === "column" || chartType === "line" || chartType === "area")
      ? trendSources.map((source) => (
          <Line
            key={`_trend_${source.dataKey}`}
            type="linear"
            dataKey={`_trend_${source.dataKey}`}
            name={
              trendSources.length > 1
                ? `${trendSeriesName} (${source.name})`
                : trendSeriesName
            }
            stroke={source.fill}
            strokeWidth={TREND_STROKE_WIDTH}
            strokeDasharray={TREND_DASH}
            strokeLinecap="round"
            strokeOpacity={1}
            dot={false}
            connectNulls
            legendType="line"
            isAnimationActive={false}
          />
        ))
      : null;

  if (chartType === "pie") {
    const primary = series[0];
    if (!primary) return null;
    const pieData = chartData.map((row) => ({
      name: String(row[categoryKey] ?? ""),
      value: Number(row[primary.dataKey]) || 0,
      fill: resolveCategoryFill(row, categoryFillKey, primary.fill),
    }));
    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height}>
        <PieChart>
          <Tooltip
            formatter={(value) =>
              value == null || Number.isNaN(Number(value))
                ? "—"
                : tooltipValue(Number(value))
            }
          />
          {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={Math.min(height * 0.35, 110)}
            onClick={(entry) => {
              if (!onCategoryClick || !entry?.name) return;
              onCategoryClick(String(entry.name));
            }}
          >
            {pieData.map((entry, index) => (
              <Cell
                key={`${entry.name}-${index}`}
                fill={
                  entry.fill ||
                  series[index % series.length]?.fill ||
                  primary.fill
                }
              />
            ))}
          </Pie>
        </PieChart>
      </StableResponsiveContainer>
    );
  }

  if (chartType === "horizontal_bar") {
    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height}>
        <BarChart data={chartData} layout="vertical" margin={margin}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
          />
          <YAxis
            type="category"
            dataKey={categoryKey}
            width={120}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
          {series.map((entry) => (
            <Bar
              key={entry.dataKey}
              dataKey={entry.dataKey}
              name={entry.name}
              fill={entry.fill}
              radius={[0, 4, 4, 0]}
              cursor={onCategoryClick ? "pointer" : undefined}
              onClick={handleBarCategoryClick}
            >
              {categoryFillKey
                ? chartData.map((row, index) => (
                    <Cell
                      key={`${entry.dataKey}-${index}`}
                      fill={resolveCategoryFill(row, categoryFillKey, entry.fill)}
                    />
                  ))
                : null}
              {barValueLabels(showValueLabels, formatY, "right")}
            </Bar>
          ))}
        </BarChart>
      </StableResponsiveContainer>
    );
  }

  if (chartType === "line") {
    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height}>
        <LineChart data={chartData} margin={margin}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            width={88}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
          {series.map((entry) => (
            <Line
              key={entry.dataKey}
              type="monotone"
              dataKey={entry.dataKey}
              name={entry.name}
              stroke={entry.fill}
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls
            />
          ))}
          {trendLines}
        </LineChart>
      </StableResponsiveContainer>
    );
  }

  if (chartType === "area") {
    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height}>
        <ComposedChart data={chartData} margin={margin}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
            tickLine={false}
          />
          <YAxis
            width={88}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => formatY(Number(value))}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
          {series.map((entry) => (
            <Area
              key={entry.dataKey}
              type="monotone"
              dataKey={entry.dataKey}
              name={entry.name}
              stroke={entry.fill}
              fill={entry.fill}
              fillOpacity={0.25}
              strokeWidth={2}
            />
          ))}
          {trendLines}
        </ComposedChart>
      </StableResponsiveContainer>
    );
  }

  // column | bar | stacked_bar
  const stackId = chartType === "stacked_bar" ? "stack" : undefined;
  const plotMargin =
    showValueLabels && !stackId
      ? { ...margin, top: Math.max(margin.top ?? 0, 28) }
      : margin;

  return (
    <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height}>
      <ComposedChart data={chartData} margin={plotMargin}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey={categoryKey}
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <YAxis
          width={88}
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatY(Number(value))}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
        {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
        {series.map((entry, index) => {
          const labelThisBar =
            showValueLabels && (!stackId || index === series.length - 1);
          return (
            <Bar
              key={entry.dataKey}
              dataKey={entry.dataKey}
              name={entry.name}
              fill={entry.fill}
              stackId={stackId}
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
              cursor={onCategoryClick ? "pointer" : undefined}
              onClick={handleBarCategoryClick}
            >
              {categoryFillKey && !stackId
                ? chartData.map((row, cellIndex) => (
                    <Cell
                      key={`${entry.dataKey}-${cellIndex}`}
                      fill={resolveCategoryFill(row, categoryFillKey, entry.fill)}
                    />
                  ))
                : null}
              {barValueLabels(labelThisBar, formatY, "top")}
            </Bar>
          );
        })}
        {trendLines}
      </ComposedChart>
    </StableResponsiveContainer>
  );
}
