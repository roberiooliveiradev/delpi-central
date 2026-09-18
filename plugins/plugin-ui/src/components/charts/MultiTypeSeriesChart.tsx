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
import {
  withLinearTrendField,
  type IncompleteBucketMode,
} from "../../utils/linearTrendSeries";
import {
  DUAL_Y_AXIS_RIGHT_WIDTH,
  dualYAxisMargin,
  hasSecondaryYAxis,
  isSecondaryYSeries,
  resolveTooltipSeries,
} from "./multiTypeSeriesDualAxis";
import { StableResponsiveContainer } from "./StableResponsiveContainer";

export type MultiTypeSeriesSpec = {
  dataKey: string;
  name: string;
  fill: string;
  /**
   * Runtime: draw OLS trend for this series (column/line/area).
   * Capability lives on `trendCapable`; this flag is the effective ON state
   * after `applySeriesViewPreferences`.
   */
  trendSource?: boolean;
  /**
   * Capability: series may receive a trend. Default true in view preferences.
   * Set false to opt out (non-temporal / non-numeric overlays).
   */
  trendCapable?: boolean;
  /**
   * When false, OLS ignores `_bucketFraction` (comparatives aligned to the
   * current axis whose prior buckets are already complete).
   */
  trendApplyIncompleteBucket?: boolean;
  /** Eixo Y direito para escalas independentes (ex.: R$ vs quantidade). */
  axis?: "primary" | "secondary";
  /** No gráfico de colunas, série secundária pode ser linha. */
  plotAs?: "bar" | "line";
  /** Override da cor da tendência (default: `fill`). */
  trendStroke?: string;
  /** Default: tracejado. */
  trendLineStyle?: "solid" | "dashed";
  /** Default: 3. */
  trendStrokeWidth?: number;
};

export type MultiTypeSeriesChartProps = {
  data: ReadonlyArray<Record<string, unknown>>;
  categoryKey: string;
  series: ReadonlyArray<MultiTypeSeriesSpec>;
  chartType: PersistedChartType;
  height?: number;
  showTrend?: boolean;
  /**
   * Incomplete (partial) buckets — default exclude from OLS fit.
   * Rows may carry fraction via `bucketFractionKey` (0..1).
   */
  incompleteBucketMode?: IncompleteBucketMode;
  /** Field on each row with bucket completeness 0..1. */
  bucketFractionKey?: string;
  trendSeriesName?: string;
  formatY?: (value: number) => string;
  formatYSecondary?: (value: number) => string;
  formatTooltipValue?: (value: number) => string;
  /**
   * dataKeys no eixo Y direito — independente de `series[].axis`, para o host
   * não perder o dual-axis se um mapper copiar só dataKey/name/fill.
   */
  secondaryDataKeys?: ReadonlyArray<string>;
  showLegend?: boolean;
  /**
   * Rótulo de valor nas barras/colunas (acima da coluna, à direita da barra) e nos pontos de linha.
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

function DualCartesianYAxes({
  hasSecondaryAxis,
  formatY,
  secondaryFormat,
  hideChrome,
  forceLeftId,
}: {
  hasSecondaryAxis: boolean;
  formatY: (value: number) => string;
  secondaryFormat: (value: number) => string;
  hideChrome?: boolean;
  forceLeftId?: boolean;
}) {
  const leftId = hasSecondaryAxis || forceLeftId ? "left" : undefined;
  return (
    <>
      <YAxis
        yAxisId={leftId}
        width={88}
        tick={{ fontSize: 12 }}
        tickFormatter={(value) => formatY(Number(value))}
        tickLine={hideChrome ? false : undefined}
        axisLine={hideChrome ? false : undefined}
      />
      {hasSecondaryAxis ? (
        <YAxis
          yAxisId="right"
          orientation="right"
          width={DUAL_Y_AXIS_RIGHT_WIDTH}
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => secondaryFormat(Number(value))}
        />
      ) : null}
    </>
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
  incompleteBucketMode = "exclude",
  bucketFractionKey = "_bucketFraction",
  trendSeriesName = "Tendência",
  formatY = defaultFormatY,
  formatYSecondary,
  formatTooltipValue,
  secondaryDataKeys,
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
    () =>
      `${series.map((entry) => entry.dataKey).join("|")}:${hasSecondaryYAxis(series, secondaryDataKeys) ? "dual" : "single"}`,
    [secondaryDataKeys, series],
  );

  const chartData = useMemo(() => {
    let rows = data.map((row) => ({ ...row }));
    const trendAllowed =
      chartType === "column" || chartType === "line" || chartType === "area";
    if (!showTrend || !trendAllowed || trendSources.length === 0) return rows;
    for (const source of trendSources) {
      const applyIncompleteBucket = source.trendApplyIncompleteBucket !== false;
      rows = withLinearTrendField(rows, source.dataKey, `_trend_${source.dataKey}`, {
        incompleteBucketMode: applyIncompleteBucket ? incompleteBucketMode : "exclude",
        fractionKey: applyIncompleteBucket ? bucketFractionKey : undefined,
      });
    }
    return rows;
  }, [
    bucketFractionKey,
    chartType,
    data,
    incompleteBucketMode,
    showTrend,
    trendSources,
  ]);

  const tooltipValue = formatTooltipValue ?? formatY;
  const secondaryFormat = formatYSecondary ?? formatY;
  const hasSecondaryAxis = hasSecondaryYAxis(series, secondaryDataKeys);
  const dualAxisMargin = dualYAxisMargin(hasSecondaryAxis, margin.right);
  const plotHostProps = {
    className: [
      "delpi-ui-multi-type-series-chart",
      hasSecondaryAxis ? "delpi-ui-multi-type-series-chart--dual-y" : "",
    ]
      .filter(Boolean)
      .join(" "),
    style: hasSecondaryAxis ? ({ overflow: "visible" } as const) : undefined,
  };

  const formatTooltip = (value: unknown, name: unknown, item: unknown): [string, string] => {
    const spec = resolveTooltipSeries(series, name, item);
    const format =
      spec && isSecondaryYSeries(spec, secondaryDataKeys)
        ? secondaryFormat
        : tooltipValue;
    return [
      value == null || Number.isNaN(Number(value)) ? "—" : format(Number(value)),
      String(name ?? ""),
    ];
  };

  const seriesAxisId = (entry: MultiTypeSeriesSpec, forceLeft: boolean) => {
    if (!hasSecondaryAxis) return forceLeft ? "left" : undefined;
    return isSecondaryYSeries(entry, secondaryDataKeys) ? "right" : "left";
  };
  const asOverlayLine = (entry: MultiTypeSeriesSpec) => entry.plotAs === "line";

  const handleBarCategoryClick = (bar: unknown) => {
    if (!onCategoryClick) return;
    const payload = (bar as { payload?: Record<string, unknown> } | null)?.payload;
    const category = payload?.[categoryKey];
    if (category != null) onCategoryClick(String(category));
  };

  const columnLike =
    chartType === "column" || chartType === "bar" || chartType === "stacked_bar";
  const trendLines =
    showTrend &&
    (chartType === "column" || chartType === "line" || chartType === "area")
      ? trendSources.map((source) => (
          <Line
            key={`_trend_${source.dataKey}`}
            yAxisId={seriesAxisId(source, columnLike)}
            type="linear"
            dataKey={`_trend_${source.dataKey}`}
            name={
              trendSources.length > 1
                ? `${trendSeriesName} (${source.name})`
                : trendSeriesName
            }
            stroke={source.trendStroke?.trim() || source.fill}
            strokeWidth={source.trendStrokeWidth ?? TREND_STROKE_WIDTH}
            strokeDasharray={
              source.trendLineStyle === "solid" ? undefined : TREND_DASH
            }
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
    const lineMargin = {
      ...(showValueLabels && series.length
        ? { ...margin, top: Math.max(margin.top ?? 0, 28) }
        : margin),
      ...dualAxisMargin,
    };
    const pointLabels = (show: boolean) => barValueLabels(show, formatY, "top");

    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height} {...plotHostProps}>
        <LineChart data={chartData} margin={lineMargin}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <DualCartesianYAxes
            hasSecondaryAxis={hasSecondaryAxis}
            formatY={formatY}
            secondaryFormat={secondaryFormat}
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
              yAxisId={seriesAxisId(entry, false)}
              type="monotone"
              dataKey={entry.dataKey}
              name={entry.name}
              stroke={entry.fill}
              strokeWidth={2}
              dot={{ r: 3 }}
              connectNulls
              legendType="line"
              isAnimationActive={false}
            >
              {pointLabels(showValueLabels)}
            </Line>
          ))}
          {trendLines}
        </LineChart>
      </StableResponsiveContainer>
    );
  }

  if (chartType === "area") {
    return (
      <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height} {...plotHostProps}>
        <ComposedChart data={chartData} margin={{ ...margin, ...dualAxisMargin }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
            tickLine={false}
          />
          <DualCartesianYAxes
            hasSecondaryAxis={hasSecondaryAxis}
            formatY={formatY}
            secondaryFormat={secondaryFormat}
            hideChrome
          />
          <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
          {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
          {series.map((entry) => {
            const axisId = seriesAxisId(entry, false);
            if (asOverlayLine(entry)) {
              return (
                <Line
                  key={entry.dataKey}
                  yAxisId={axisId}
                  type="monotone"
                  dataKey={entry.dataKey}
                  name={entry.name}
                  stroke={entry.fill}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  connectNulls
                  legendType="line"
                  isAnimationActive={false}
                />
              );
            }
            return (
              <Area
                key={entry.dataKey}
                yAxisId={axisId}
                type="monotone"
                dataKey={entry.dataKey}
                name={entry.name}
                stroke={entry.fill}
                fill={entry.fill}
                fillOpacity={0.25}
                strokeWidth={2}
              />
            );
          })}
          {trendLines}
        </ComposedChart>
      </StableResponsiveContainer>
    );
  }

  // column | bar | stacked_bar
  const stackId = chartType === "stacked_bar" ? "stack" : undefined;
  const plotMargin = {
    ...margin,
    ...dualAxisMargin,
    ...(showValueLabels && !stackId
      ? { top: Math.max(margin.top ?? 0, 28) }
      : {}),
  };

  return (
    <StableResponsiveContainer key={seriesOrderKey} width="100%" height={height} {...plotHostProps}>
      <ComposedChart data={chartData} margin={plotMargin}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey={categoryKey}
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          tickLine={false}
        />
        <DualCartesianYAxes
          hasSecondaryAxis={hasSecondaryAxis}
          formatY={formatY}
          secondaryFormat={secondaryFormat}
          hideChrome
          forceLeftId
        />
        <Tooltip
            formatter={formatTooltip}
            labelFormatter={(label) => String(label)}
          />
        {/* null: ordem do array `series` (default Recharts ordena por label e desalinha das barras) */}
          {showLegend ? <Legend itemSorter={null} /> : null}
        {series.map((entry, index) => {
          const axisId = seriesAxisId(entry, true);
          const asLine = asOverlayLine(entry);
          if (asLine) {
            return (
              <Line
                key={entry.dataKey}
                yAxisId={axisId}
                type="monotone"
                dataKey={entry.dataKey}
                name={entry.name}
                stroke={entry.fill}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
                legendType="line"
                isAnimationActive={false}
              />
            );
          }
          const labelThisBar =
            showValueLabels && (!stackId || index === series.length - 1);
          return (
            <Bar
              key={entry.dataKey}
              yAxisId={axisId}
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
