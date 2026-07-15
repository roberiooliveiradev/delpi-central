import { useMemo, useState } from "react";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { ClientesTable } from "../features/customers/ClientesTable";
import { DelayRangesChart } from "../features/dashboard/DelayRangesChart";
import { MonthlyEvolutionChart } from "../features/dashboard/MonthlyEvolutionChart";
import { PeriodFilters } from "../features/dashboard/PeriodFilters";
import { SummaryCards } from "../features/dashboard/SummaryCards";
import { TopLateCustomersChart } from "../features/dashboard/TopLateCustomersChart";
import { TopLateCustomersModal } from "../features/dashboard/TopLateCustomersModal";
import { CustomerTitlesModal } from "../features/titles/CustomerTitlesModal";
import {
  defaultClientesTableState,
  useInadimplenciaClientes,
  type ClientesTableState,
} from "../hooks/useInadimplenciaClientes";
import { useInadimplenciaDashboard } from "../hooks/useInadimplenciaDashboard";
import type { PeriodFormState, SelectedCustomer } from "../types/inadimplencia";
import {
  createDefaultPeriodFormState,
  formatPeriodLabel,
  periodFilterFromForm,
  validatePeriodRange,
} from "../utils/period";

export function InadimplenciaPage() {
  const [periodForm, setPeriodForm] = useState<PeriodFormState>(() =>
    createDefaultPeriodFormState(),
  );
  const [appliedPeriodForm, setAppliedPeriodForm] = useState<PeriodFormState>(() =>
    createDefaultPeriodFormState(),
  );
  const [clientesTable, setClientesTable] = useState<ClientesTableState>(
    defaultClientesTableState,
  );
  const [selectedCustomer, setSelectedCustomer] = useState<SelectedCustomer | null>(null);
  const [topClientesOpen, setTopClientesOpen] = useState(false);
  const [localValidation, setLocalValidation] = useState<string | null>(null);

  const periodFilter = useMemo(
    () => periodFilterFromForm(appliedPeriodForm),
    [appliedPeriodForm],
  );

  const dashboard = useInadimplenciaDashboard(periodFilter);
  const clientes = useInadimplenciaClientes(periodFilter, clientesTable);

  const applyPeriod = (next: PeriodFormState) => {
    if (next.preset === "custom") {
      const error = validatePeriodRange(next.startDate, next.endDate);
      setLocalValidation(error);
      if (error) return;
    } else {
      setLocalValidation(null);
    }
    setAppliedPeriodForm(next);
    setClientesTable((current) => ({ ...current, page: 1 }));
  };

  const handlePeriodChange = (next: PeriodFormState) => {
    setPeriodForm(next);
    if (next.preset !== "custom") {
      applyPeriod(next);
    } else {
      setLocalValidation(validatePeriodRange(next.startDate, next.endDate));
    }
  };

  const showInitialLoading = dashboard.isLoading && !dashboard.data.resumo;
  const periodLabel =
    dashboard.data.resumo?.periodo.rotulo ?? formatPeriodLabel(appliedPeriodForm);

  return (
    <div className="dashboard-financeiro-inadimplencia fi-page dashboard-page">
      <PageHeader
        title="Indicador de Inadimplência"
        subtitle="Acompanhe a pontualidade dos recebimentos e identifique clientes e títulos com maior impacto financeiro."
        periodLabel={periodLabel}
        updatedAt={dashboard.updatedAt}
        onRefresh={dashboard.reload}
        refreshing={dashboard.isLoading}
      />

      <PeriodFilters
        value={periodForm}
        disabled={dashboard.isLoading}
        validationError={localValidation}
        onChange={handlePeriodChange}
        onApplyCustom={() => applyPeriod(periodForm)}
      />

      {dashboard.state === "error" ? (
        <ErrorState
          message={dashboard.error ?? "Falha ao carregar dados."}
          onRetry={dashboard.reload}
        />
      ) : null}

      {showInitialLoading ? <LoadingState message="Carregando painel…" /> : null}

      {!showInitialLoading && dashboard.state !== "error" ? (
        <>
          <SummaryCards
            mensal={dashboard.data.mensal}
            topClienteMes={dashboard.data.topClienteMes}
            loading={dashboard.isLoading}
            onOpenTopClientes={() => setTopClientesOpen(true)}
          />

          <MonthlyEvolutionChart
            period={periodFilter}
            mensal={dashboard.data.mensal}
            loading={dashboard.isLoading}
          />

          <div className="fi-charts-grid">
            <DelayRangesChart faixas={dashboard.data.faixas} loading={dashboard.isLoading} />
            <TopLateCustomersChart onOpenRanking={() => setTopClientesOpen(true)} />
          </div>

          <ClientesTable
            period={periodFilter}
            periodLabel={periodLabel}
            data={clientes.data}
            loading={clientes.isLoading}
            error={clientes.error}
            search={clientesTable.search}
            sortBy={clientesTable.sortBy}
            sortDir={clientesTable.sortDir}
            onlyWithDelays={clientesTable.onlyWithDelays}
            onSearchChange={(value) =>
              setClientesTable((current) => ({ ...current, search: value, page: 1 }))
            }
            onSortChange={(sortBy, sortDir) =>
              setClientesTable((current) => ({ ...current, sortBy, sortDir, page: 1 }))
            }
            onOnlyWithDelaysChange={(value) =>
              setClientesTable((current) => ({
                ...current,
                onlyWithDelays: value,
                page: 1,
              }))
            }
            onPageChange={(page) => setClientesTable((current) => ({ ...current, page }))}
            onOpenTitles={(customer) =>
              setSelectedCustomer({
                cliente_codigo: customer.cliente_codigo,
                loja: customer.loja,
                nome_cliente: customer.nome_cliente,
                nome_reduzido: customer.nome_reduzido,
                titulos_atraso: customer.titulos_atraso,
                valor_atraso: customer.valor_atraso,
              })
            }
            onRetry={clientes.reload}
          />
        </>
      ) : null}

      <CustomerTitlesModal
        open={Boolean(selectedCustomer)}
        customer={selectedCustomer}
        period={periodFilter}
        onClose={() => setSelectedCustomer(null)}
      />

      <TopLateCustomersModal
        open={topClientesOpen}
        onClose={() => setTopClientesOpen(false)}
      />
    </div>
  );
}
