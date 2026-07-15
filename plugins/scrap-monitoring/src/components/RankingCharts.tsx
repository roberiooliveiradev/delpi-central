import {
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
  CHART_RANKING_HEIGHT,
  CHART_Y_AXIS_WIDTH,
  PIE_COLORS,
} from "../constants/chartTheme";
import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapRankingItem } from "../types/scrap";
import { formatCurrencyBrl, formatShortLabel } from "../utils/formatters";
import { ChartCard } from "./ChartCard";

type RankingChartsProps = {
  motivos: ScrapRankingItem[];
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
  payload?: Array<{ name?: string; value?: number }>;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0];
  return (
    <div className="sm-chart-tooltip">
      <strong>{row.name}</strong>
      <div>{formatCurrencyBrl(row.value)}</div>
    </div>
  );
}

function HorizontalValueBars({ items }: { items: ScrapRankingItem[] }) {
  const data = items.map((item) => ({
    name: item.label || item.code,
    value: item.value,
  }));

  return (
    <ResponsiveContainer width="100%" height={CHART_RANKING_HEIGHT}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
        <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={CHART_AXIS_TICK} tickFormatter={(v) => formatCurrencyBrl(Number(v))} />
        <YAxis
          type="category"
          dataKey="name"
          width={CHART_Y_AXIS_WIDTH}
          tick={CHART_AXIS_TICK}
          tickFormatter={(v) => formatShortLabel(String(v), 42)}
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
  }));

  return (
    <ResponsiveContainer width="100%" height={CHART_RANKING_HEIGHT}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={95}
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
          wrapperStyle={{ fontSize: 12, maxWidth: 280 }}
          formatter={(value) => formatShortLabel(String(value), 36)}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function RankingCharts({
  motivos,
  materiais,
  produtos,
  centros,
  colaboradores,
}: RankingChartsProps) {
  return (
    <div className={CHARTS_GRID_CLASS}>
      <ChartCard title="Motivo" titleHint={CHARTS.motivo} empty={motivos.length === 0}>
        <MotivoPie items={motivos} />
      </ChartCard>
      <ChartCard
        title="Top 10 por matéria-prima"
        titleHint={CHARTS.materiaPrima}
        empty={materiais.length === 0}
      >
        <HorizontalValueBars items={materiais} />
      </ChartCard>
      <ChartCard
        title="Top 10 por produto acabado"
        titleHint={CHARTS.produtoAcabado}
        empty={produtos.length === 0}
      >
        <HorizontalValueBars items={produtos} />
      </ChartCard>
      <ChartCard
        title="Por centro de trabalho"
        titleHint={CHARTS.centroTrabalho}
        empty={centros.length === 0}
      >
        <HorizontalValueBars items={centros} />
      </ChartCard>
      <ChartCard
        title="Top 10 por colaborador"
        titleHint={CHARTS.colaborador}
        empty={colaboradores.length === 0}
      >
        <HorizontalValueBars items={colaboradores} />
      </ChartCard>
    </div>
  );
}
