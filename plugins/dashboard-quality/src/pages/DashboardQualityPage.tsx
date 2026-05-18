import { useMemo } from "react";
import {
  ClipboardCheck,
  Factory,
  Lightbulb,
  Truck,
} from "lucide-react";

import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { ModuleShortcut, PPM_SHORTCUT_HREF } from "../components/ModuleShortcut";
import { SummaryCard } from "../components/SummaryCard";
import { QUALITY_ROUTES } from "../constants/routes";
import { useQualityBranches } from "../hooks/useQualityBranches";
import { useQualityDashboard } from "../hooks/useQualityDashboard";
import { useQualityFilters } from "../hooks/useQualityFilters";
import {
  formatCurrency,
  formatDecimal,
  formatInteger,
  formatPpm,
  formatScore,
} from "../utils/format";
import { formatPeriodLabel } from "../utils/dates";

const MODULE_SHORTCUTS = [
  {
    title: "PPM detalhado",
    description: "Listagem interna e externa com paginação.",
    href: PPM_SHORTCUT_HREF,
  },
  {
    title: "Não conformidades",
    description: "Consulta analítica de NC no Protheus.",
    href: QUALITY_ROUTES.nonconformities,
  },
  {
    title: "Kaizens",
    description: "Lista e filtros por status e setor.",
    href: QUALITY_ROUTES.kaizen,
  },
  {
    title: "Auditoria 5S",
    description: "Histórico e notas por área.",
    href: QUALITY_ROUTES.audit5s,
  },
] as const;

type DashboardQualityPageProps = {
  pathname?: string;
};

export function DashboardQualityPage({ pathname }: DashboardQualityPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
  } = useQualityFilters();

  const { branches, loading: branchesLoading } = useQualityBranches(apiParams);

  const {
    ppmInternal,
    ppmExternal,
    kaizen,
    audit5s,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  } = useQualityDashboard(apiParams);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const isBusy = loading || refreshing;

  return (
    <div className="dashboard-quality dashboard-page">
      <FilterBar
        currentPath={pathname ?? QUALITY_ROUTES.home}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        branches={branches}
        branchesLoading={branchesLoading}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onRefresh={reload}
        refreshing={refreshing}
      />

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button className="dq-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dq-state dq-state--warning" role="status">
          <p>Alguns indicadores não carregaram. Os demais permanecem disponíveis.</p>
        </div>
      ) : null}

      {loading && !ppmInternal ? (
        <div className="dq-state dq-state--loading" aria-live="polite">
          Carregando indicadores…
        </div>
      ) : null}

      <section className="dq-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title="PPM interno"
          value={formatPpm(ppmInternal?.ppm)}
          subtitle={`Devolvido: ${formatDecimal(ppmInternal?.total_devolvido_un)} un · ${periodLabel}`}
          icon={<Factory size={22} />}
          loading={isBusy && !ppmInternal}
        />
        <KpiCard
          title="PPM externo"
          value={formatPpm(ppmExternal?.ppm)}
          subtitle={`Devolvido: ${formatDecimal(ppmExternal?.total_devolvido_un)} un · ${periodLabel}`}
          icon={<Truck size={22} />}
          loading={isBusy && !ppmExternal}
        />
      </section>

      <section className="dq-summary-grid" aria-busy={isBusy}>
        <SummaryCard
          title="Kaizens"
          description="Resumo de melhorias implementadas no período."
          icon={<Lightbulb size={22} />}
          loading={isBusy && !kaizen}
          metrics={[
            {
              label: "Total de kaizens",
              value: formatInteger(kaizen?.total_kaizens),
            },
            {
              label: "Economia acumulada",
              value: formatCurrency(kaizen?.total_savings),
            },
            {
              label: "Registros na lista",
              value: formatInteger(kaizen?.list_kaizen.length ?? 0),
            },
          ]}
        />
        <SummaryCard
          title="Auditoria 5S"
          description="Média de notas das auditorias realizadas."
          icon={<ClipboardCheck size={22} />}
          loading={isBusy && !audit5s}
          metrics={[
            {
              label: "Nota média",
              value: formatScore(audit5s?.average_score),
            },
            {
              label: "Auditorias no período",
              value: formatInteger(audit5s?.list_audits.length ?? 0),
            },
            {
              label: "Período",
              value: periodLabel,
            },
          ]}
        />
      </section>

      <section className="dq-shortcuts-section">
        <h2 className="dq-section-title">Módulos</h2>
        <div className="dq-shortcuts-grid">
          {MODULE_SHORTCUTS.map((item) => (
            <ModuleShortcut key={item.title} {...item} filterState={filterState} />
          ))}
        </div>
      </section>
    </div>
  );
}
