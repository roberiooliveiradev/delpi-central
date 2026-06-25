import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchRecurrenceGroups } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { RecurrenceTable } from "../components/RecurrenceTable";
import { StateAlert } from "../components/StateAlert";
import { FilterBar } from "../components/ui/FilterBar";
import { MultiSelectField } from "../components/ui/MultiSelectField";
import { SelectField } from "../components/ui/SelectField";
import {
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
} from "../constants/actionPlans";
import type { RecurrenceGroup } from "../types/recurrence";

type Props = {
  onNavigate: (path: string) => void;
};

const MIN_PLANS_OPTIONS = [
  { value: "2", label: "2 ou mais planos" },
  { value: "3", label: "3 ou mais planos" },
  { value: "5", label: "5 ou mais planos" },
];

export function RecurrencePage({ onNavigate }: Props) {
  const [items, setItems] = useState<RecurrenceGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [scope, setScope] = useState("");
  const [minPlans, setMinPlans] = useState("2");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecurrenceGroups({
        branch_code: branches.length === 1 ? branches[0] : undefined,
        nonconformity_scope: scope || undefined,
        min_plans: Number(minPlans),
        page_size: 200,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar recorrência.");
    } finally {
      setLoading(false);
    }
  }, [branches, minPlans, scope]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleItems = useMemo(() => {
    if (branches.length <= 1) return items;
    return items.filter((group) => branches.includes(group.branch_code ?? ""));
  }, [branches, items]);

  const scopeOptions = [
    { value: "", label: "Todos os escopos" },
    ...PAC_NONCONFORMITY_SCOPES.map((item) => ({ value: item.value, label: item.label })),
  ];

  return (
    <>
      <PageHeader
        title="Recorrência de falhas"
        subtitle="Agrupamento por produto e modo de falha (mesma chave de recorrência)."
      />
      <AppNav active="recurrence" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <FilterBar compact>
        <MultiSelectField
          id="pac-recurrence-branch"
          label="Filial"
          options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
          selectedValues={branches}
          onChange={setBranches}
          emptyLabel="Todas"
          searchable={false}
        />
        <SelectField
          id="pac-recurrence-scope"
          label="Escopo NC"
          options={scopeOptions}
          value={scope}
          onChange={setScope}
          searchable={false}
        />
        <SelectField
          id="pac-recurrence-min"
          label="Mínimo de planos"
          options={MIN_PLANS_OPTIONS}
          value={minPlans}
          onChange={setMinPlans}
          searchable={false}
        />
      </FilterBar>

      <section className="pac-card">
        <RecurrenceTable
          items={visibleItems}
          loading={loading}
          emptyMessage="Nenhum grupo com recorrência no filtro atual."
          onNavigate={onNavigate}
        />
      </section>
    </>
  );
}
