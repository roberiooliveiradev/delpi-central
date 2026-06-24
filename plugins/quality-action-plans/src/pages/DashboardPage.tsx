import { useCallback, useEffect, useState } from "react";

import { fetchDashboard } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { DashboardCards } from "../components/DashboardCards";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { listPath, overduePath, PAC_BRANCH_OPTIONS } from "../constants/actionPlans";
import type { DashboardSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function DashboardPage({ onNavigate }: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branchCode, setBranchCode] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard(branchCode || undefined);
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard.");
    } finally {
      setLoading(false);
    }
  }, [branchCode]);

  useEffect(() => {
    void load();
  }, [load]);

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
          </>
        }
      />
      <AppNav active="dashboard" onNavigate={onNavigate} />
      <div className="pac-filters-row pac-filters-row--compact">
        <div className="pac-filter-box">
          <label htmlFor="pac-dashboard-branch">Filial</label>
          <select
            id="pac-dashboard-branch"
            value={branchCode}
            onChange={(event) => setBranchCode(event.target.value)}
          >
            <option value="">Consolidado</option>
            {PAC_BRANCH_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && !summary ? <p className="pac-muted">Carregando indicadores…</p> : null}
      {summary ? <DashboardCards summary={summary} /> : null}
    </>
  );
}
