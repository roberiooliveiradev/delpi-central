import { useMemo } from "react";
import {
  BarChart3,
  Percent,
  Target,
  UserPlus,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "../components/ChartCard";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { CHART_COLORS } from "../constants/chartColors";
import { useCommercialDashboard } from "../hooks/useCommercialDashboard";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { formatPeriodLabel } from "../utils/dates";
import { formatDecimal, formatInteger, formatPercent } from "../utils/format";

const CHART_HEIGHT = 280;

type DashboardCommercialPageProps = {
  pathname?: string;
};

export function DashboardCommercialPage(_props: DashboardCommercialPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useCommercialFilters();

  const {
    headOfficeRol,
    branchRol,
    closingRate,
    newClientsAverage,
    newClientsRol,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useCommercialDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const isBusy = loading || refreshing;
  const hasData = headOfficeRol !== null || branchRol !== null;

  const rolChartData = useMemo(
    () => [
      {
        name: "Matriz (01)",
        meta: headOfficeRol?.rol_target_pct ?? 0,
      },
      {
        name: "Filial (02)",
        meta: branchRol?.rol_target_pct ?? 0,
      },
    ],
    [headOfficeRol?.rol_target_pct, branchRol?.rol_target_pct]
  );

  const conversionChartData = useMemo(
    () =>
      closingRate
        ? [
            { name: "Propostas", value: closingRate.qtd_proposals },
            { name: "Ganhas", value: closingRate.qtd_won },
          ]
        : [],
    [closingRate]
  );

  const printDisabled = loading && !hasData;

  return (
    <div className="dashboard-commercial dashboard-page dc-print-root">
      <FilterBar
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        printDisabled={printDisabled}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />

      <TotvsSourceBanner />

      {error ? (
        <div className="dc-state dc-state--error" role="alert">
          <p>{error}</p>
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dc-state dc-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}

      {loading && !hasData ? (
        <div className="dc-state dc-state--loading" aria-live="polite">
          Carregando indicadores…
        </div>
      ) : null}

      <section className="dc-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="Meta ROL — Matriz"
          value={formatPercent(headOfficeRol?.rol_target_pct)}
          subtitle={`ROL: ${formatDecimal(headOfficeRol?.rol)} · ${periodLabel}`}
          icon={<Target size={22} />}
          loading={isBusy && !headOfficeRol}
        />
        <KpiCard
          title="Meta ROL — Filial"
          value={formatPercent(branchRol?.rol_target_pct)}
          subtitle={`ROL: ${formatDecimal(branchRol?.rol)} · filial 02`}
          icon={<Target size={22} />}
          loading={isBusy && !branchRol}
        />
        <KpiCard
          title="Taxa de conversão"
          value={formatPercent(closingRate?.sales_conversion_rate_pct)}
          subtitle={`${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas`}
          icon={<Percent size={22} />}
          loading={isBusy && !closingRate}
        />
        <KpiCard
          title="Média mensal — clientes novos"
          value={formatDecimal(newClientsAverage?.monthly_average)}
          subtitle={`Total: ${formatInteger(newClientsAverage?.total_new_clients)} em ${formatInteger(newClientsAverage?.qtd_months)} meses`}
          icon={<UserPlus size={22} />}
          loading={isBusy && !newClientsAverage}
        />
        <KpiCard
          title="% ROL — clientes novos"
          value={formatPercent(newClientsRol?.new_clients_rol_pct)}
          subtitle={branch ? `Filial ${branch}` : "Todas as filiais"}
          icon={<Users size={22} />}
          loading={isBusy && !newClientsRol}
        />
      </section>

      <section className="dc-charts-grid">
        <ChartCard
          title="Meta ROL (% da meta)"
          hint="Matriz (01) e filial (02) no período selecionado."
        >
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={rolChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="meta" name="% meta" radius={[8, 8, 0, 0]}>
                {rolChartData.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Funil de conversão"
          hint="Propostas versus vendas ganhas no período."
        >
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={conversionChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" name="Quantidade" fill={CHART_COLORS[0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>

      <section className="dc-summary-grid dc-no-print">
        <article className="dc-card">
          <div className="dc-summary-card__header">
            <BarChart3 size={22} aria-hidden />
            <h2 className="dc-summary-card__title">Sobre os indicadores</h2>
          </div>
          <p className="dc-summary-card__description">
            Metas de ROL usam filiais fixas na API (01 matriz, 02 filial).
            Conversão e clientes novos respeitam o filtro de filial quando
            informado.
          </p>
        </article>
      </section>
    </div>
  );
}
