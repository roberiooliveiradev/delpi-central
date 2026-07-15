import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
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
  formatRankingAxisLabel,
  formatSharePercent,
  formatShortLabel,
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

function HorizontalValueBars({
  items,
  includeCode = false,
}: {
  items: ScrapRankingItem[];
  includeCode?: boolean;
}) {
  const data = items.map((item) => ({
    name: includeCode
      ? formatRankingAxisLabel(item.code, item.label, 40)
      : formatShortLabel(item.label || item.code, 36),
    fullName: includeCode
      ? `${item.code}${item.label ? ` — ${item.label}` : ""}`
      : item.label || item.code,
    value: item.value,
    sharePct: item.sharePct,
  }));

  return (
    <ResponsiveContainer width="100%" height={CHART_RANKING_HEIGHT}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 12, top: 8, bottom: 8 }}>
        <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={CHART_AXIS_TICK} tickFormatter={(v) => formatCurrencyBrl(Number(v))} />
        <YAxis
          type="category"
          dataKey="name"
          width={CHART_Y_AXIS_WIDTH}
          tick={CHART_AXIS_TICK}
          interval={0}
        />
        <Tooltip content={<CurrencyTooltip />} />
        <Bar dataKey="value" fill={CHART_COLORS.primary} radius={[0, 6, 6, 0]} />
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
        wide={false}
      >
        <HorizontalValueBars items={materiais} includeCode />
      </ChartCard>
      <ChartCard
        title="Top 10 por produto acabado"
        titleHint={CHARTS.produtoAcabado}
        empty={produtos.length === 0}
        wide={false}
      >
        <HorizontalValueBars items={produtos} includeCode />
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
