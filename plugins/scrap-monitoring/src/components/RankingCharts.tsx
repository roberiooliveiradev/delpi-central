import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { chartsGridBemClasses } from "@delpi/plugin-ui/index";

import {
  CHART_AXIS_TICK,
  CHART_COLORS,
  CHART_GRID_STROKE,
  CHART_PRODUCT_Y_AXIS_WIDTH,
  CHART_SERIES_HEIGHT_MIN,
  CHART_Y_AXIS_WIDTH,
  PIE_COLORS,
  resolveMotivoChartHeight,
  resolveMotivoPieRadii,
  resolveRankingChartHeight,
} from "../constants/chartTheme";
import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapRankingItem, ScrapSeriePoint } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatSharePercent,
  formatShortLabel,
  splitRankingAxisLines,
} from "../utils/formatters";
import { ChartCard } from "./ChartCard";

type RankingChartsProps = {
  motivos: ScrapRankingItem[];
  serie: ScrapSeriePoint[];
  serieGranularity: "day" | "month" | null;
  materiais: ScrapRankingItem[];
  produtos: ScrapRankingItem[];
  centros: ScrapRankingItem[];
  colaboradores: ScrapRankingItem[];
};

const CHARTS = SCRAP_HELP_TOOLTIPS.charts;
const CHARTS_GRID_CLASS = chartsGridBemClasses("sm");

function CurrencyTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; payload?: Record<string, unknown> }>;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0];
  const share = row.payload?.sharePct;
  return (
    <div className="sm-chart-tooltip">
      <strong>{String(row.payload?.fullName ?? row.name ?? "")}</strong>
      <div>{formatCurrencyBrl(row.value)}</div>
      {typeof share === "number" ? <div>{formatSharePercent(share)}</div> : null}
    </div>
  );
}

type ProductTickProps = {
  x?: number;
  y?: number;
  payload?: { value?: string };
  linesByKey: Map<string, { codeLine: string; descLine: string }>;
};

function ProductAxisTick({ x = 0, y = 0, payload, linesByKey }: ProductTickProps) {
  const key = String(payload?.value ?? "");
  const lines = linesByKey.get(key) ?? { codeLine: key, descLine: "" };
  const hasDesc = Boolean(lines.descLine);

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={-6}
        y={hasDesc ? -7 : 4}
        textAnchor="end"
        className="sm-chart-axis-code"
      >
        {lines.codeLine}
      </text>
      {hasDesc ? (
        <text x={-6} y={11} textAnchor="end" className="sm-chart-axis-desc">
          {lines.descLine}
        </text>
      ) : null}
    </g>
  );
}

function HorizontalValueBars({
  items,
  variant = "simple",
}: {
  items: ScrapRankingItem[];
  variant?: "simple" | "product";
}) {
  const isProduct = variant === "product";
  const linesByKey = new Map<string, { codeLine: string; descLine: string }>();

  const data = items.map((item, index) => {
    if (isProduct) {
      const key = `${item.code || item.label || index}`;
      const lines = splitRankingAxisLines(item.code, item.label, 52);
      linesByKey.set(key, lines);
      return {
        name: key,
        fullName: `${item.code}${item.label ? ` — ${item.label}` : ""}`,
        value: item.value,
        sharePct: item.sharePct,
      };
    }

    return {
      name: formatShortLabel(item.label || item.code, 28),
      fullName: item.label || item.code,
      value: item.value,
      sharePct: item.sharePct,
    };
  });

  const height = resolveRankingChartHeight(items.length, variant);
  const yWidth = isProduct ? CHART_PRODUCT_Y_AXIS_WIDTH : CHART_Y_AXIS_WIDTH;

  return (
    <div className="sm-chart-fill" style={{ minHeight: height }}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 8, right: isProduct ? 72 : 16, top: 8, bottom: 8 }}
          barCategoryGap={isProduct ? "18%" : "22%"}
        >
          <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            tick={CHART_AXIS_TICK}
            tickFormatter={(v) => formatCurrencyBrl(Number(v))}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={yWidth}
            interval={0}
            tick={
              isProduct
                ? (props) => <ProductAxisTick {...props} linesByKey={linesByKey} />
                : { ...CHART_AXIS_TICK, fontSize: 13 }
            }
          />
          <Tooltip content={<CurrencyTooltip />} />
          <Bar dataKey="value" fill={CHART_COLORS.primary} radius={[0, 6, 6, 0]} maxBarSize={28}>
            {isProduct ? (
              <LabelList
                dataKey="value"
                position="right"
                formatter={(v: number) => formatCurrencyBrl(v)}
                className="sm-chart-bar-label"
              />
            ) : null}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function MotivoPie({ items }: { items: ScrapRankingItem[] }) {
  const data = items.map((item, index) => ({
    name: item.label || item.code,
    value: item.value,
    sharePct: item.sharePct,
    fullName: item.label || item.code,
    color: PIE_COLORS[index % PIE_COLORS.length],
  }));

  const height = resolveMotivoChartHeight(items.length);
  const { innerRadius, outerRadius } = resolveMotivoPieRadii(height);
  const pieBox = Math.min(280, Math.max(180, Math.floor(height * 0.72)));

  return (
    <div className="sm-motivo-chart" style={{ minHeight: height }}>
      <div className="sm-motivo-chart__pie" style={{ width: pieBox, height: pieBox }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              paddingAngle={2}
            >
              {data.map((entry, index) => (
                <Cell key={index} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CurrencyTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="sm-motivo-chart__legend" aria-label="Legenda por motivo">
        {data.map((entry) => (
          <li key={entry.name} className="sm-motivo-chart__legend-item">
            <span
              className="sm-motivo-chart__swatch"
              style={{ background: entry.color }}
              aria-hidden
            />
            <span className="sm-motivo-chart__legend-text">
              <span className="sm-motivo-chart__legend-name">
                {formatShortLabel(entry.name, 36)}
              </span>
              <span className="sm-motivo-chart__legend-meta">
                {formatCurrencyBrl(entry.value)} ({formatSharePercent(entry.sharePct)})
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SerieChart({
  points,
  granularity,
  height,
}: {
  points: ScrapSeriePoint[];
  granularity: "day" | "month" | null;
  height: number;
}) {
  const data = points.map((point) => ({
    name: point.label,
    fullName: point.label,
    value: point.value,
  }));

  const subtitle =
    granularity === "month" ? "Agregação mensal" : granularity === "day" ? "Agregação diária" : undefined;
  const chartHeight = Math.max(CHART_SERIES_HEIGHT_MIN, height);

  return (
    <div className="sm-chart-fill" style={{ minHeight: chartHeight }}>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <AreaChart data={data} margin={{ left: 8, right: 12, top: 8, bottom: 8 }}>
          <defs>
            <linearGradient id="smSerieFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.35} />
              <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={CHART_AXIS_TICK} minTickGap={28} />
          <YAxis
            tick={CHART_AXIS_TICK}
            width={72}
            tickFormatter={(v) => formatCurrencyBrl(Number(v))}
          />
          <Tooltip content={<CurrencyTooltip />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke={CHART_COLORS.primary}
            fill="url(#smSerieFill)"
            strokeWidth={2}
            name={subtitle ?? "Valor"}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RankingCharts({
  motivos,
  serie,
  serieGranularity,
  materiais,
  produtos,
  centros,
  colaboradores,
}: RankingChartsProps) {
  const serieHint =
    serieGranularity === "month"
      ? `${CHARTS.serie} Agregado por mês (período longo).`
      : CHARTS.serie;
  const pairHeight = resolveMotivoChartHeight(motivos.length);

  return (
    <div className={CHARTS_GRID_CLASS}>
      <ChartCard
        title="Motivo"
        titleHint={CHARTS.motivo}
        empty={motivos.length === 0}
        wide={false}
        className="sm-chart-card--motivo"
      >
        <MotivoPie items={motivos} />
      </ChartCard>
      <ChartCard
        title="Evolução temporal"
        titleHint={serieHint}
        empty={serie.length === 0}
        wide={false}
        className="sm-chart-card--serie"
      >
        <SerieChart points={serie} granularity={serieGranularity} height={pairHeight} />
      </ChartCard>
      <ChartCard
        title="Top 10 por matéria-prima"
        titleHint={CHARTS.materiaPrima}
        empty={materiais.length === 0}
        wide
      >
        <HorizontalValueBars items={materiais} variant="product" />
      </ChartCard>
      <ChartCard
        title="Top 10 por produto acabado"
        titleHint={CHARTS.produtoAcabado}
        empty={produtos.length === 0}
        wide
      >
        <HorizontalValueBars items={produtos} variant="product" />
      </ChartCard>
      <ChartCard
        title="Por centro de trabalho"
        titleHint={CHARTS.centroTrabalho}
        empty={centros.length === 0}
        wide={false}
      >
        <HorizontalValueBars items={centros} />
      </ChartCard>
      <ChartCard
        title="Top 10 por colaborador"
        titleHint={CHARTS.colaborador}
        empty={colaboradores.length === 0}
        wide={false}
      >
        <HorizontalValueBars items={colaboradores} />
      </ChartCard>
    </div>
  );
}
