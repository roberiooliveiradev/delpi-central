import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchOverduePlans } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { PlansTable } from "../components/PlansTable";
import { StateAlert } from "../components/StateAlert";
import { FilterBar } from "../components/ui/FilterBar";
import { MultiSelectField } from "../components/ui/MultiSelectField";
import { PAC_BRANCH_OPTIONS } from "../constants/actionPlans";
import type { ActionPlanSummary } from "../types/actionPlan";

type Props = {
  onNavigate: (path: string) => void;
};

export function OverduePage({ onNavigate }: Props) {
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOverduePlans({
        branch_code: branches.length === 1 ? branches[0] : undefined,
        page_size: 200,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar planos atrasados.");
    } finally {
      setLoading(false);
    }
  }, [branches]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleItems = useMemo(() => {
    if (branches.length <= 1) return items;
    return items.filter((plan) => branches.includes(plan.branch_code ?? ""));
  }, [branches, items]);

  return (
    <>
      <PageHeader
        title="Planos com atraso"
        subtitle="Planos com ações vencidas e ainda não concluídas."
      />
      <AppNav active="overdue" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <FilterBar compact>
        <MultiSelectField
          id="pac-overdue-branch"
          label="Filial"
          options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
          selectedValues={branches}
          onChange={setBranches}
          emptyLabel="Todas"
          searchable={false}
        />
      </FilterBar>

      <section className="pac-card">
        <PlansTable
          items={visibleItems}
          loading={loading}
          emptyMessage="Nenhum plano com ações atrasadas."
          onNavigate={onNavigate}
        />
      </section>
    </>
  );
}
