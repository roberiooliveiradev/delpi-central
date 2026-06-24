import { useCallback, useEffect, useState } from "react";

import { fetchOverduePlans } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { PlansTable } from "../components/PlansTable";
import { StateAlert } from "../components/StateAlert";
import type { ActionPlanSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function OverduePage({ onNavigate }: Props) {
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOverduePlans({ page_size: 100 });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar planos atrasados.");
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
        title="Planos com atraso"
        subtitle="Planos com ações vencidas e ainda não concluídas."
      />
      <AppNav active="overdue" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      <section className="pac-card">
        <PlansTable
          items={items}
          loading={loading}
          emptyMessage="Nenhum plano com ações atrasadas."
          onNavigate={onNavigate}
        />
      </section>
    </>
  );
}
