import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
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
  CHART_MOTIVO_HEIGHT,
  CHART_MOTIVO_INNER_RADIUS,
  CHART_MOTIVO_OUTER_RADIUS,
  CHART_PRODUCT_RANKING_HEIGHT,
  CHART_PRODUCT_Y_AXIS_WIDTH,
  CHART_RANKING_HEIGHT,
  CHART_SERIES_HEIGHT,
  CHART_Y_AXIS_WIDTH,
  PIE_COLORS,
} from "../constants/chartTheme";
import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapRankingItem, ScrapSeriePoint } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatMotivoLegendLabel,
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

  const height = isProduct ? CHART_PRODUCT_RANKING_HEIGHT : CHART_RANKING_HEIGHT;
  const yWidth = isProduct ? CHART_PRODUCT_Y_AXIS_WIDTH : CHART_Y_AXIS_WIDTH;

  return (
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
  );
}

function MotivoPie({ items }: { items: ScrapRankingItem[] }) {
  const data = items.map((item) => ({
    name: item.label || item.code,
    value: item.value,
    sharePct: item.sharePct,
    fullName: item.label || item.code,
  }));

  const legendLookup = new Map(
    data.map((item) => [item.name, { value: item.value, sharePct: item.sharePct }]),
  );

  return (
    <ResponsiveContainer width="100%" height={CHART_MOTIVO_HEIGHT}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="36%"
          cy="50%"
          innerRadius={CHART_MOTIVO_INNER_RADIUS}
          outerRadius={CHART_MOTIVO_OUTER_RADIUS}
          paddingAngle={2}
        >
          {data.map((_, index) => (
            <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CurrencyTooltip />} />
        <Legend
          layout="vertical"
          align="right"
          verticalAlign="middle"
          wrapperStyle={{
            fontSize: 14,
            fontWeight: 600,
            maxWidth: 280,
            lineHeight: "1.55",
            paddingLeft: 8,
          }}
          formatter={(value) => {
            const stats = legendLookup.get(String(value));
            if (!stats) return formatShortLabel(String(value), 32);
            return formatMotivoLegendLabel(String(value), stats.value, stats.sharePct);
          }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

function SerieChart({
  points,
  granularity,
}: {
  points: ScrapSeriePoint[];
  granularity: "day" | "month" | null;
}) {
  const data = points.map((point) => ({
    name: point.label,
    fullName: point.label,
    value: point.value,
  }));

  const subtitle =
    granularity === "month" ? "Agregação mensal" : granularity === "day" ? "Agregação diária" : undefined;

  return (
    <ResponsiveContainer width="100%" height={CHART_SERIES_HEIGHT}>
      <AreaChart data={data} margin={{ left: 8, right: 12, top: 8, bottom: 8 }}>
        <defs>
          <linearGradient id="smSerieFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.35} />
            <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={CHART_AXIS_TICK} minTickGap={28} />
        <YAxis tick={CHART_AXIS_TICK} width={72} tickFormatter={(v) => formatCurrencyBrl(Number(v))} />
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

  return (
    <div className={CHARTS_GRID_CLASS}>
      <ChartCard
        title="Motivo"
        titleHint={CHARTS.motivo}
        empty={motivos.length === 0}
        wide={false}
        className="sm-chart-card--compact"
      >
        <MotivoPie items={motivos} />
      </ChartCard>
      <ChartCard
        title="Evolução temporal"
        titleHint={serieHint}
        empty={serie.length === 0}
        wide={false}
      >
        <SerieChart points={serie} granularity={serieGranularity} />
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
