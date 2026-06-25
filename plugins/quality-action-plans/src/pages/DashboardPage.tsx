import { useCallback, useEffect, useState } from "react";

import { fetchActionPlans, fetchDashboard } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { DashboardEffectivenessCharts } from "../components/dashboard/DashboardEffectivenessCharts";
import { DashboardRecurrenceAlertCard } from "../components/dashboard/DashboardRecurrenceAlertCard";
import { DashboardRankingCharts } from "../components/dashboard/DashboardRankingCharts";
import { DashboardBreakdownCharts } from "../components/dashboard/DashboardBreakdownCharts";
import { DashboardCharts } from "../components/dashboard/DashboardCharts";
import { DashboardKpis } from "../components/dashboard/DashboardKpis";
import { DashboardTimingKpis } from "../components/dashboard/DashboardTimingKpis";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { SelectField } from "../components/ui/SelectField";
import { FilterBar } from "../components/ui/FilterBar";
import { listPath, overduePath, recurrencePath, PAC_BRANCH_OPTIONS, PAC_NONCONFORMITY_SCOPES } from "../constants/actionPlans";
import type { ActionPlanSummary, DashboardSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function DashboardPage({ onNavigate }: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [plans, setPlans] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branchCode, setBranchCode] = useState("");
  const [scope, setScope] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardData, plansData] = await Promise.all([
        fetchDashboard(branchCode || undefined, scope || undefined),
        fetchActionPlans({
          branch_code: branchCode || undefined,
          nonconformity_scope: scope || undefined,
          page_size: 200,
        }),
      ]);
      setSummary(dashboardData);
      setPlans(plansData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard.");
    } finally {
      setLoading(false);
    }
  }, [branchCode, scope]);

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

  return (
    <>
      <PageHeader
        title="Resumo executivo"
        subtitle="Indicadores consolidados dos planos de ação de qualidade."
        actions={
          <>
            <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(listPath())}>
              Ver todos os planos
            </button>
            <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(overduePath())}>
              Ver atrasados
            </button>
            <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(recurrencePath())}>
              Ver recorrência
            </button>
          </>
        }
      />
      <AppNav active="dashboard" onNavigate={onNavigate} />

      <FilterBar compact>
        <SelectField
          id="pac-dashboard-branch"
          label="Filial"
          options={branchOptions}
          value={branchCode}
          onChange={setBranchCode}
          searchable
        />
        <SelectField
          id="pac-dashboard-scope"
          label="Escopo NC"
          options={scopeOptions}
          value={scope}
          onChange={setScope}
          searchable={false}
        />
      </FilterBar>

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && !summary ? <p className="pac-muted">Carregando indicadores…</p> : null}

      {summary ? (
        <>
          <DashboardKpis summary={summary} loading={loading} />
          <DashboardTimingKpis timing={summary.timing} loading={loading} />
          <DashboardRecurrenceAlertCard
            alert={summary.recurrence_alert}
            loading={loading}
            onNavigate={onNavigate}
          />
          <DashboardBreakdownCharts breakdowns={summary.breakdowns} />
          <DashboardEffectivenessCharts
            effectiveness={summary.effectiveness_by_action_type}
            loading={loading}
          />
          <DashboardRankingCharts rankings={summary.rankings} />
          <DashboardCharts summary={summary} plans={plans} />
        </>
      ) : null}
    </>
  );
}
