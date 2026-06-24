import { useCallback, useEffect, useState } from "react";

import { fetchDashboard } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { DashboardCards } from "../components/DashboardCards";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { listPath, overduePath } from "../constants/actionPlans";
import type { DashboardSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function DashboardPage({ onNavigate }: Props) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboard();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

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
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && !summary ? <p className="pac-muted">Carregando indicadores…</p> : null}
      {summary ? <DashboardCards summary={summary} /> : null}
    </>
  );
}
