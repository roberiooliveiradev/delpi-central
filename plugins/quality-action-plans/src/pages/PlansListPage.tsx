import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchActionPlans } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PlansFilters } from "../components/filters/PlansFilters";
import { PageHeader } from "../components/PageHeader";
import { PlansTable } from "../components/PlansTable";
import { StateAlert } from "../components/StateAlert";
import { newPlanPath } from "../constants/actionPlans";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import type { ActionPlanSummary } from "../types/actionPlan";
import {
  applyClientPlanFilters,
  buildListApiParams,
  EMPTY_PLANS_FILTERS,
  needsClientSideFilter,
  type PlansFilterState,
} from "../utils/planFilters";
import { PAC_SECTION } from "../components/ui/stateChrome";

type Props = {
  onNavigate: (path: string) => void;
};

export function PlansListPage({ onNavigate }: Props) {
  const [items, setItems] = useState<ActionPlanSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<PlansFilterState>(EMPTY_PLANS_FILTERS);

  const debouncedCustomer = useDebouncedValue(filters.customerName);
  const debouncedProduct = useDebouncedValue(filters.productCode);
  const debouncedOwner = useDebouncedValue(filters.ownerUserId);
  const debouncedDepartment = useDebouncedValue(filters.department);
  const debouncedRootCause = useDebouncedValue(filters.rootCauseCategory);

  const apiFilters = useMemo(
    (): PlansFilterState => ({
      ...filters,
      customerName: debouncedCustomer,
      productCode: debouncedProduct,
      ownerUserId: debouncedOwner,
      department: debouncedDepartment,
      rootCauseCategory: debouncedRootCause,
    }),
    [
      filters,
      debouncedCustomer,
      debouncedProduct,
      debouncedOwner,
      debouncedDepartment,
      debouncedRootCause,
    ],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActionPlans(buildListApiParams(apiFilters));
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar planos.");
    } finally {
      setLoading(false);
    }
  }, [apiFilters]);

  useEffect(() => {
    void load();
  }, [load]);

  const visibleItems = useMemo(() => {
    if (!needsClientSideFilter(apiFilters)) {
      return items;
    }
    return applyClientPlanFilters(items, apiFilters);
  }, [apiFilters, items]);

  return (
    <>
      <PageHeader
        title="Planos de ação"
        subtitle="Listagem consolidada para acompanhamento da liderança."
        actions={
          <button type="button" className="pac-primary-btn" onClick={() => onNavigate(newPlanPath())}>
            Novo plano
          </button>
        }
      />
      <AppNav active="list" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <PlansFilters
        filters={filters}
        onChange={setFilters}
        onRefresh={() => void load()}
        loading={loading}
      />

      <section className="pac-card">
        <div className={`${PAC_SECTION.header} pac-table-header`}>
          <h2 className={PAC_SECTION.title}>Resultados</h2>
          <span className="pac-muted pac-table-header__count">
            {visibleItems.length} plano(s)
          </span>
        </div>
        <PlansTable items={visibleItems} loading={loading} onNavigate={onNavigate} />
      </section>
    </>
  );
}
