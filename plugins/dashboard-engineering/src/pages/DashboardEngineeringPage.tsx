import { useMemo } from "react";
import { BarChart3, CircleGauge, Clock, Coins, Lightbulb, Percent } from "lucide-react";

import { DataSourceBanner } from "../components/DataSourceBanner";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut } from "../components/ModuleShortcut";
import { EngineeringStatusAlerts } from "../components/EngineeringStatusAlerts";
import { ENGINEERING_ROUTES } from "../constants/routes";
import { useEngineeringDashboard } from "../hooks/useEngineeringDashboard";
import { useEngineeringFilters } from "../hooks/useEngineeringFilters";
import { useSimulatedLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { formatPeriodLabel } from "../utils/dates";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPercent,
} from "../utils/format";

const SHORTCUTS = [
  {
    title: "LMPs no prazo",
    description: "Gráficos, status por nível e lista de propostas/LMPs.",
    href: ENGINEERING_ROUTES.lmp,
  },
  {
    title: "TRANSFORMA+",
    description: "Ganhos, ROI, processos e economia diária na planilha.",
    href: ENGINEERING_ROUTES.transforma,
  },
] as const;

type DashboardEngineeringPageProps = {
  pathname?: string;
};

export function DashboardEngineeringPage({ pathname }: DashboardEngineeringPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useEngineeringFilters();

  const {
    transforma,
    lmpSummary,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useEngineeringDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );
  const branchLabel = branch ? `Filial ${branch}` : "Consolidado";
  const isBusy = loading || refreshing;
  const hasData = transforma !== null || lmpSummary !== null;
  const refreshLoadingProgress = useSimulatedLoadingProgress(refreshing && hasData);

  return (
    <div className="dashboard-engineering dashboard-page">
      <FilterBar
        subtitle="Indicadores estratégicos de engenharia (LMP e TRANSFORMA+)"
        currentPath={pathname ?? ENGINEERING_ROUTES.home}
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />
      <DataSourceBanner variant="all" />
      <EngineeringStatusAlerts
        error={error}
        loading={loading}
        hasData={hasData}
        onRetry={reload}
      />
      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando visão geral"
          description="Atualizando KPIs de LMP e TRANSFORMA+."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}
      {Object.keys(sectionErrors).length > 0 && hasData ? (
        <div className="ds-state ds-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}
      <section className="ds-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="% LMP dentro do prazo"
          value={formatPercent(lmpSummary?.percent_dentro_prazo, 2)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<CircleGauge size={22} />}
          loading={isBusy && !lmpSummary}
        />
        <KpiCard
          title="Lead time médio (dias úteis)"
          value={formatDecimal(lmpSummary?.avg_lead_time, 2)}
          subtitle="Média no período"
          icon={<Clock size={22} />}
          loading={isBusy && !lmpSummary}
        />
        <KpiCard
          title="Total de propostas"
          value={formatInteger(
            lmpSummary?.total_items ?? lmpSummary?.total_lmps
          )}
          subtitle="LMPs / amostras no recorte"
          icon={<BarChart3 size={22} />}
          loading={isBusy && !lmpSummary}
        />
        <KpiCard
          title="Ganhos brutos TRANSFORMA+"
          value={formatCurrency(transforma?.total_gross_savings_in_period)}
          subtitle={`${branchLabel} · ${periodLabel}`}
          icon={<Coins size={22} />}
          loading={isBusy && !transforma}
        />
        <KpiCard
          title="Soluções implementadas"
          value={formatInteger(transforma?.implemented_solutions_count)}
          subtitle="Melhorias na planilha"
          icon={<Lightbulb size={22} />}
          loading={isBusy && !transforma}
        />
        <KpiCard
          title="ROI médio TRANSFORMA+"
          value={formatPercent(transforma?.average_roi, 1)}
          subtitle="No período filtrado"
          icon={<Percent size={22} />}
          loading={isBusy && !transforma}
        />
      </section>
      <section className="ds-shortcuts-grid">
        {SHORTCUTS.map((item) => (
          <ModuleShortcut
            key={item.href}
            title={item.title}
            description={item.description}
            href={item.href}
            filterState={filterState}
          />
        ))}
      </section>
    </div>
  );
}
