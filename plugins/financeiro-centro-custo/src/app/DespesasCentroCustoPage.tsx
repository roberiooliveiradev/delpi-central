import { useMemo, useState } from "react";

import {
  MonthlyEvolutionChart,
  RankingCentrosChart,
  RankingFornecedoresChart,
} from "../components/Charts";
import { DespesasFilters } from "../components/DespesasFilters";
import { ErrorState } from "../components/ErrorState";
import { LancamentosTable } from "../components/LancamentosTable";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { SummaryCards } from "../components/SummaryCards";
import {
  defaultLancamentosTableState,
  useLancamentosCentroCusto,
} from "../hooks/useLancamentosCentroCusto";
import { useDespesasCentroCustoDashboard } from "../hooks/useDespesasCentroCustoDashboard";
import type { FilterFormState } from "../types/despesasCentroCusto";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
} from "../utils/dateRange";

function mergeFilterChange(
  current: FilterFormState,
  patch: Partial<FilterFormState>,
): FilterFormState {
  const next: FilterFormState = { ...current, ...patch };

  if ("branch" in patch && patch.branch !== current.branch) {
    next.costCenter = "";
    next.supplierKey = "";
  }

  if ("costCenter" in patch && patch.costCenter !== current.costCenter) {
    next.supplierKey = "";
  }

  return next;
}

export function DespesasCentroCustoPage() {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [filters, setFilters] = useState<FilterFormState>(defaultFilters);
  const [tableState, setTableState] = useState(defaultLancamentosTableState);

  const appliedFilters = useMemo(() => filtersFromFormState(filters), [filters]);

  const dashboard = useDespesasCentroCustoDashboard(appliedFilters);
  const lancamentos = useLancamentosCentroCusto(appliedFilters, tableState);

  const handleFilterChange = (patch: Partial<FilterFormState>) => {
    setFilters((current) => mergeFilterChange(current, patch));
    setTableState((current) => ({ ...current, page: 1 }));
  };

  const handleClearFilters = () => {
    const cleared = createDefaultFilterFormState();
    setFilters(cleared);
    setTableState(defaultLancamentosTableState);
  };

  const showInitialLoading = dashboard.isLoading && !dashboard.data.resumo;

  return (
    <div className="fcc-page">
      <PageHeader
        title="Despesas por Centro de Custo"
        subtitle="Acompanhe gastos, evolução mensal, centros de custo e fornecedores com maior impacto."
      />

      <DespesasFilters
        filters={filters}
        options={dashboard.data.filtros}
        loading={dashboard.isLoading}
        onChange={handleFilterChange}
        onClear={handleClearFilters}
      />

      {dashboard.state === "error" ? (
        <ErrorState message={dashboard.error ?? "Falha ao carregar dados."} onRetry={dashboard.reload} />
      ) : null}

      {showInitialLoading ? <LoadingState message="Carregando painel…" /> : null}

      {!showInitialLoading && dashboard.state !== "error" ? (
        <>
          <SummaryCards resumo={dashboard.data.resumo} loading={dashboard.isLoading} />

          <div className="fcc-charts-grid">
            <MonthlyEvolutionChart serie={dashboard.data.serie} loading={dashboard.isLoading} />
            {!appliedFilters.costCenter ? (
              <RankingCentrosChart
                ranking={dashboard.data.rankingCentros}
                filters={appliedFilters}
                loading={dashboard.isLoading}
              />
            ) : null}
            <RankingFornecedoresChart
              ranking={dashboard.data.rankingFornecedores}
              filters={appliedFilters}
              loading={dashboard.isLoading}
            />
          </div>

          <LancamentosTable
            data={lancamentos.data}
            loading={lancamentos.isLoading}
            error={lancamentos.error}
            search={tableState.search}
            sortBy={tableState.sortBy}
            sortDir={tableState.sortDir}
            onSearchChange={(value) =>
              setTableState((current) => ({ ...current, search: value, page: 1 }))
            }
            onSearchSubmit={() => {
              setTableState((current) => ({ ...current, page: 1 }));
            }}
            onSortChange={(sortBy, sortDir) =>
              setTableState((current) => ({ ...current, sortBy, sortDir, page: 1 }))
            }
            onPageChange={(page) => setTableState((current) => ({ ...current, page }))}
            onRetry={lancamentos.reload}
          />
        </>
      ) : null}
    </div>
  );
}
