import { useMemo } from "react";
import {
  Banknote,
  BarChart3,
  Building2,
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
import {
  buildRolKpiSubtitle,
  formatChartCurrency,
  formatCurrency,
  formatCurrencyCompact,
  formatDecimal,
  formatInteger,
  formatPercent,
  isMeaningfulRolTarget,
} from "../utils/format";
import type { RolTargetData } from "../types/commercial";

const CHART_HEIGHT = 280;

type DashboardCommercialPageProps = {
  pathname?: string;
};

function rolPctValue(
  rol: RolTargetData | null | undefined
): number | null {
  if (!rol || !isMeaningfulRolTarget(rol.target)) return null;
  const pct = rol.rol_target_pct;
  if (pct == null || Number.isNaN(pct) || pct < 0 || pct > 500) return null;
  return pct;
}

function rolCurrencyChartRows(
  headOffice: RolTargetData | null,
  branch: RolTargetData | null
) {
  return [
    {
      name: "Matriz (01)",
      rol: headOffice?.rol ?? 0,
      pct: rolPctValue(headOffice),
    },
    {
      name: "Filial (02)",
      rol: branch?.rol ?? 0,
      pct: rolPctValue(branch),
    },
  ];
}

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

  const rolCurrencyChart = useMemo(
    () => rolCurrencyChartRows(headOfficeRol, branchRol),
    [headOfficeRol, branchRol]
  );

  const rolPctChart = useMemo(
    () => rolCurrencyChart.filter((row) => row.pct != null),
    [rolCurrencyChart]
  );

  const showRolPctChart =
    isMeaningfulRolTarget(headOfficeRol?.target) ||
    isMeaningfulRolTarget(branchRol?.target);

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
          title="ROL — Matriz (01)"
          value={formatCurrency(headOfficeRol?.rol)}
          subtitle={buildRolKpiSubtitle(
            headOfficeRol?.rol,
            headOfficeRol?.target,
            headOfficeRol?.rol_target_pct,
            periodLabel
          )}
          icon={<Banknote size={22} />}
          loading={isBusy && !headOfficeRol}
        />
        <KpiCard
          title="ROL — Filial (02)"
          value={formatCurrency(branchRol?.rol)}
          subtitle={buildRolKpiSubtitle(
            branchRol?.rol,
            branchRol?.target,
            branchRol?.rol_target_pct,
            "Filial 02"
          )}
          icon={<Building2 size={22} />}
          loading={isBusy && !branchRol}
        />
        <KpiCard
          title="Taxa de conversão"
          value={formatPercent(closingRate?.sales_conversion_rate_pct)}
          subtitle={`${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${periodLabel}`}
          icon={<Percent size={22} />}
          loading={isBusy && !closingRate}
        />
        <KpiCard
          title="Média mensal — clientes novos"
          value={formatDecimal(newClientsAverage?.monthly_average, 1)}
          subtitle={`Total ${formatInteger(newClientsAverage?.total_new_clients)} em ${formatInteger(newClientsAverage?.qtd_months)} meses · ${periodLabel}`}
          icon={<UserPlus size={22} />}
          loading={isBusy && !newClientsAverage}
        />
        <KpiCard
          title="% ROL — clientes novos"
          value={formatPercent(newClientsRol?.new_clients_rol_pct)}
          subtitle={branch ? `Filial ${branch} · ${periodLabel}` : periodLabel}
          icon={<Users size={22} />}
          loading={isBusy && !newClientsRol}
        />
      </section>

      <section className="dc-charts-grid">
        <ChartCard
          title="ROL realizada (R$)"
          hint="Receita operacional líquida com IPI no período — matriz e filial."
        >
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={rolCurrencyChart}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(v) => formatCurrencyCompact(v)} width={72} />
              <Tooltip
                formatter={(value) => {
                  if (value == null) return ["—", "ROL"];
                  const n = typeof value === "number" ? value : Number(value);
                  return [formatChartCurrency(n), "ROL"];
                }}
              />
              <Bar dataKey="rol" name="ROL" radius={[8, 8, 0, 0]}>
                {rolCurrencyChart.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {showRolPctChart ? (
          <ChartCard
            title="% da meta ROL"
            hint="Percentual do ROL realizado em relação à meta configurada."
          >
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={rolPctChart}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  formatter={(value) => {
                    if (value == null || typeof value !== "number") {
                      return ["—", "% da meta"];
                    }
                    return [formatPercent(value), "% da meta"];
                  }}
                />
                <Bar dataKey="pct" name="% da meta" radius={[8, 8, 0, 0]}>
                  {rolPctChart.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        ) : (
          <ChartCard
            title="% da meta ROL"
            hint="Meta de referência ainda não configurada no backend (valor simbólico)."
          >
            <div className="dc-state-box">
              O percentual da meta será exibido quando os valores de meta (target)
              estiverem configurados na api-delpi. O ROL em reais permanece acima.
            </div>
          </ChartCard>
        )}

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
            <Target size={22} aria-hidden />
            <h2 className="dc-summary-card__title">Como ler os indicadores</h2>
          </div>
          <p className="dc-summary-card__description">
            <strong>ROL</strong> é valor monetário (R$) com IPI. Matriz usa filial
            01 e comparativo de filial 02. A taxa de conversão e os clientes novos
            respeitam o filtro de filial quando informado.
          </p>
        </article>
        <article className="dc-card">
          <div className="dc-summary-card__header">
            <BarChart3 size={22} aria-hidden />
            <h2 className="dc-summary-card__title">Metas ROL</h2>
          </div>
          <p className="dc-summary-card__description">
            O % da meta só aparece quando a meta cadastrada na API é representativa
            (evita distorção com meta placeholder). Ajuste os valores DEFAULT_*_TARGET
            no commercial_composer da api-delpi para habilitar o gráfico de %.
          </p>
        </article>
      </section>
    </div>
  );
}
