import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CircleGauge,
  Package,
  Percent,
  TrendingUp,
  Warehouse,
} from "lucide-react";

import { ChartCard } from "../components/ChartCard";
import { DataSourceBanner } from "../components/DataSourceBanner";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { CHART_COLORS } from "../constants/chartColors";
import { useSuppliesDashboard } from "../hooks/useSuppliesDashboard";
import { useSuppliesFilters } from "../hooks/useSuppliesFilters";
import { formatPeriodLabel } from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

const CHART_HEIGHT = 300;

function formatMonthLabel(item: { month_date?: string; month?: string; year?: string }) {
  if (item.month_date) {
    const d = new Date(item.month_date);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleDateString("pt-BR", { month: "short", year: "2-digit" });
    }
  }
  if (item.month && item.year) return `${item.month}/${item.year}`;
  return item.month ?? "—";
}

export function DashboardSuppliesPage() {
  const {
    dateStart,
    dateEnd,
    branch,
    location,
    setDateStart,
    setDateEnd,
    setBranch,
    setLocation,
    periodParams,
    stockParams,
  } = useSuppliesFilters();

  const {
    cpv,
    otd,
    stockValue,
    inventoryTurnover,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useSuppliesDashboard({ periodParams, stockParams });

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const locationLabel = location ? `Local ${location}` : "Todas as localizações";

  const isBusy = loading || refreshing;
  const hasData =
    cpv !== null || otd !== null || stockValue !== null || inventoryTurnover !== null;

  const cpvByCfopChart = useMemo(
    () =>
      (cpv?.by_cfop ?? []).map((item) => ({
        name: item.cfop ?? "—",
        value: Number(item.cpv_total ?? 0),
      })),
    [cpv?.by_cfop]
  );

  const otdMonthlyChart = useMemo(
    () =>
      [...(otd?.monthly_breakdown ?? [])]
        .reverse()
        .map((item) => ({
          name: formatMonthLabel(item),
          otd: Number(item.otd_percentage ?? 0),
        })),
    [otd?.monthly_breakdown]
  );

  const stockByLocationChart = useMemo(
    () =>
      (stockValue?.by_location ?? []).map((item) => ({
        name: item.location ?? "—",
        value: Number(item.total_stock_value ?? 0),
      })),
    [stockValue?.by_location]
  );

  const lateSuppliersChart = useMemo(
    () =>
      (otd?.top_late_suppliers ?? []).slice(0, 8).map((item) => ({
        name:
          item.supplier_name ??
          item.supplier ??
          item.supplier_code ??
          "Fornecedor",
        value: Number(item.late_lines ?? 0),
      })),
    [otd?.top_late_suppliers]
  );

  return (
    <div className="dashboard-supplies dashboard-page">
      <FilterBar
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        location={location}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onLocationChange={setLocation}
        onRefresh={reload}
        refreshing={refreshing}
      />

      <DataSourceBanner />

      {error ? (
        <div className="ds-state ds-state--error" role="alert">
          <p>{error}</p>
          <button className="ds-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="ds-state ds-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}

      {loading && !hasData ? (
        <div className="ds-state ds-state--loading" aria-live="polite">
          Carregando indicadores…
        </div>
      ) : null}

      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="CPV total"
          value={formatCurrency(cpv?.summary.cpv_total)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !cpv}
        />
        <KpiCard
          title="CPV / ROL"
          value={formatPercent(cpv?.summary.cpv_percentage)}
          subtitle={`ROL ${formatCurrency(cpv?.summary.rol_with_ipi)} · ${periodLabel}`}
          icon={<Percent size={22} />}
          loading={isBusy && !cpv}
        />
        <KpiCard
          title="OTD compras"
          value={formatPercent(otd?.summary.otd_percentage)}
          subtitle={`${formatInteger(otd?.summary.on_time_lines)} no prazo / ${formatInteger(otd?.summary.total_lines)} linhas · ${periodLabel}`}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !otd}
        />
        <KpiCard
          title="Valor de estoque"
          value={formatCurrency(stockValue?.summary.total_stock_value)}
          subtitle={`${branchLabel} · ${locationLabel}`}
          icon={<Warehouse size={22} />}
          loading={isBusy && !stockValue}
        />
        <KpiCard
          title="Giro IDD (meses)"
          value={formatDecimal(
            inventoryTurnover?.summary.inventory_turnover_months,
            2
          )}
          subtitle={`${branchLabel} · ${locationLabel} · ${periodLabel}`}
          icon={<Package size={22} />}
          loading={isBusy && !inventoryTurnover}
        />
      </section>

      <section className="ds-charts-grid">
        <ChartCard title="CPV por CFOP" hint="Distribuição do custo de produto vendido.">
          {cpvByCfopChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={cpvByCfopChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(v) => formatCurrency(Number(v))} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="CPV (R$)">
                  {cpvByCfopChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem dados de CPV no período.</div>
          )}
        </ChartCard>

        <ChartCard title="OTD mensal" hint="Pontualidade de entregas de compras.">
          {otdMonthlyChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={otdMonthlyChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis unit="%" domain={[0, 100]} />
                <Tooltip
                  formatter={(value) =>
                    formatPercent(typeof value === "number" ? value : Number(value))
                  }
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="otd"
                  name="OTD %"
                  stroke={CHART_COLORS[0]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem série mensal de OTD.</div>
          )}
        </ChartCard>

        <ChartCard title="Estoque por localização" hint="Posição atual (sem filtro de data).">
          {stockByLocationChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={stockByLocationChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v))} />
                <YAxis type="category" dataKey="name" width={100} />
                <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                <Bar dataKey="value" name="Valor (R$)" fill={CHART_COLORS[1]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Sem saldo por localização.</div>
          )}
        </ChartCard>

        <ChartCard title="Fornecedores com mais atrasos" hint="Linhas em atraso no período.">
          {lateSuppliersChart.length > 0 ? (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={lateSuppliersChart} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={120} />
                <Tooltip />
                <Bar dataKey="value" name="Linhas atrasadas" fill={CHART_COLORS[2]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="ds-state-box">Nenhum fornecedor crítico no período.</div>
          )}
        </ChartCard>
      </section>

      <section className="ds-summary-grid">
        <article className="ds-card">
          <div className="ds-summary-card__header">
            <Package size={22} aria-hidden />
            <h2 className="ds-summary-card__title">Como ler os indicadores</h2>
          </div>
          <p className="ds-summary-card__description">
            <strong>CPV</strong> soma custos de saída (SD3) sobre o ROL do período.
            <strong> OTD</strong> mede linhas de compras recebidas no prazo.
            <strong> Estoque</strong> é snapshot atual por filial/local.
            <strong> IDD</strong> (giro em meses) usa estoque ÷ CPV médio mensal — períodos
            parciais são mensalizados; use mês fechado para análise oficial.
          </p>
        </article>
      </section>
    </div>
  );
}
