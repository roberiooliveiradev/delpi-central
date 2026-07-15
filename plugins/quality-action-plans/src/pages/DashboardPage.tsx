import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchActionPlans, fetchDashboard } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { DashboardEffectivenessCharts } from "../components/dashboard/DashboardEffectivenessCharts";
import { DashboardEffectivenessPendingCard } from "../components/dashboard/DashboardEffectivenessPendingCard";
import { DashboardRecurrenceAlertCard } from "../components/dashboard/DashboardRecurrenceAlertCard";
import { DashboardStalledAlertCard } from "../components/dashboard/DashboardStalledAlertCard";
import { DashboardRankingCharts } from "../components/dashboard/DashboardRankingCharts";
import { DashboardBreakdownCharts } from "../components/dashboard/DashboardBreakdownCharts";
import { DashboardCharts } from "../components/dashboard/DashboardCharts";
import { DashboardKpis } from "../components/dashboard/DashboardKpis";
import { DashboardTimingKpis } from "../components/dashboard/DashboardTimingKpis";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { SelectField } from "../components/ui/SelectField";
import { TextField } from "../components/ui/TextField";
import { FilterBar } from "../components/ui/FilterBar";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { listPath, overduePath, recurrencePath, PAC_BRANCH_OPTIONS, PAC_NONCONFORMITY_SCOPES } from "../constants/actionPlans";
import type { ActionPlanSummary, DashboardSummary } from "../types/actionPlan";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import {
  buildDashboardApiParams,
  EMPTY_DASHBOARD_FILTERS,
  type DashboardFilterState,
} from "../utils/dashboardFilters";
import { usePacPermissions } from "../context/PacPermissionsContext";
import { PAC_GHOST_BTN } from "../components/ui/ghostChrome";

type Props = {
  onNavigate: (path: string) => void;
};

export function DashboardPage({ onNavigate }: Props) {
  const { canValidateEffectiveness } = usePacPermissions();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [plans, setPlans] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilterState>(EMPTY_DASHBOARD_FILTERS);

  const debouncedCustomer = useDebouncedValue(filters.customerName);
  const debouncedProduct = useDebouncedValue(filters.productCode);
  const debouncedFailureMode = useDebouncedValue(filters.failureMode);

  const apiFilters = useMemo(
    (): DashboardFilterState => ({
      ...filters,
      customerName: debouncedCustomer,
      productCode: debouncedProduct,
      failureMode: debouncedFailureMode,
    }),
    [filters, debouncedCustomer, debouncedProduct, debouncedFailureMode],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const query = buildDashboardApiParams(apiFilters);
      const [dashboardData, plansData] = await Promise.all([
        fetchDashboard(query),
        fetchActionPlans({ ...query, page_size: 200 }),
      ]);
      setSummary(dashboardData);
      setPlans(plansData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard.");
    } finally {
      setLoading(false);
    }
  }, [apiFilters]);

  useEffect(() => {
    void load();
  }, [load]);

  const branchOptions = [
    { value: "", label: "Consolidado (todas)" },
    ...PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label })),
  ];

  const scopeOptions = [
    { value: "", label: "Todos os escopos" },
    ...PAC_NONCONFORMITY_SCOPES.map((item) => ({ value: item.value, label: item.label })),
  ];

  function patchFilters(partial: Partial<DashboardFilterState>) {
    setFilters((current) => ({ ...current, ...partial }));
  }

  return (
    <>
      <PageHeader
        title="Resumo executivo"
        subtitle="Indicadores consolidados dos planos de ação de qualidade."
        actions={
          <>
            <button type="button" className={PAC_GHOST_BTN} onClick={() => onNavigate(listPath())}>
              Ver todos os planos
            </button>
            <button type="button" className={PAC_GHOST_BTN} onClick={() => onNavigate(overduePath())}>
              Ver atrasados
            </button>
            <button type="button" className={PAC_GHOST_BTN} onClick={() => onNavigate(recurrencePath())}>
              Ver recorrência
            </button>
          </>
        }
      />
      <AppNav active="dashboard" onNavigate={onNavigate} />

      <FilterBar>
        <SelectField
          id="pac-dashboard-branch"
          label="Filial"
          hint={PAC_HELP_TOOLTIPS.filters.branch}
          options={branchOptions}
          value={filters.branchCode}
          onChange={(branchCode) => patchFilters({ branchCode })}
          searchable
        />
        <SelectField
          id="pac-dashboard-scope"
          label="Escopo NC"
          hint={PAC_HELP_TOOLTIPS.filters.scope}
          options={scopeOptions}
          value={filters.scope}
          onChange={(scope) => patchFilters({ scope })}
          searchable={false}
        />
        <TextField
          id="pac-dashboard-customer"
          label="Cliente"
          hint={PAC_HELP_TOOLTIPS.filters.customer}
          value={filters.customerName}
          onChange={(customerName) => patchFilters({ customerName })}
          placeholder="Filtrar por cliente"
          type="search"
        />
        <TextField
          id="pac-dashboard-product"
          label="Produto"
          hint={PAC_HELP_TOOLTIPS.filters.product}
          value={filters.productCode}
          onChange={(productCode) => patchFilters({ productCode })}
          placeholder="Código do produto"
          type="search"
        />
        <TextField
          id="pac-dashboard-failure-mode"
          label="Modo de falha"
          hint={PAC_HELP_TOOLTIPS.filters.failureMode}
          value={filters.failureMode}
          onChange={(failureMode) => patchFilters({ failureMode })}
          placeholder="Ex.: oxidação, trinca"
          type="search"
        />
      </FilterBar>

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && !summary ? <p className="pac-muted">Carregando indicadores…</p> : null}

      {summary ? (
        <div className="pac-page-stack">
          <DashboardKpis summary={summary} loading={loading} />
          <DashboardTimingKpis timing={summary.timing} loading={loading} />
          <DashboardRecurrenceAlertCard
            alert={summary.recurrence_alert}
            loading={loading}
            onNavigate={onNavigate}
          />
          <DashboardStalledAlertCard
            alert={summary.stalled_alert}
            loading={loading}
            onNavigate={onNavigate}
          />
          {canValidateEffectiveness ? (
            <DashboardEffectivenessPendingCard
              alert={summary.effectiveness_pending_alert}
              loading={loading}
              onNavigate={onNavigate}
            />
          ) : null}
          <DashboardBreakdownCharts breakdowns={summary.breakdowns} />
          <DashboardEffectivenessCharts
            effectiveness={summary.effectiveness_by_action_type}
            loading={loading}
          />
          <DashboardRankingCharts rankings={summary.rankings} />
          <DashboardCharts summary={summary} plans={plans} />
        </div>
      ) : null}
    </>
  );
}
