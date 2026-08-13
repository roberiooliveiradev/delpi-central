import { RefreshCw } from "lucide-react";

import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialStateBanner,
} from "../../../../app/commercialUi";
import type { UseCustomerBillingResult } from "../hooks/useCustomerBilling";
import { CustomerBillingFilters } from "./CustomerBillingFilters";
import { CustomerBillingSummaryCards } from "./CustomerBillingSummaryCards";
import { CustomerInvoicesTable } from "./CustomerInvoicesTable";

type CustomerBillingPanelProps = {
  billing: UseCustomerBillingResult;
  basePath: string;
  codigo: string;
  loja: string;
};

export function CustomerBillingPanel({
  billing,
  basePath,
  codigo,
  loja,
}: CustomerBillingPanelProps) {
  const {
    loading,
    refreshing,
    error,
    validationError,
    hasData,
    data,
    preset,
    setPreset,
    startDate,
    endDate,
    setStartDate,
    setEndDate,
    situation,
    setSituation,
    search,
    setSearch,
    page,
    setPage,
    reload,
  } = billing;

  const showInitialLoading = loading && !hasData;
  const empty =
    !loading && !error && !validationError && data && data.invoices.length === 0;

  return (
    <div className="cm-customer-billing-panel">
      <header className="cm-customer-billing-panel__header">
        <h2 className="cm-customer-section-title">
          Faturamento e notas fiscais
        </h2>
        <CommercialActionButton
          variant="ghost"
          onClick={reload}
          disabled={loading || refreshing || Boolean(validationError)}
          aria-busy={refreshing || loading}
        >
          <RefreshCw size={16} aria-hidden="true" className={refreshing ? "cm-spin" : undefined} />
          {refreshing || loading ? "Atualizando…" : "Atualizar"}
        </CommercialActionButton>
      </header>

      <CustomerBillingFilters
        preset={preset}
        startDate={startDate}
        endDate={endDate}
        situation={situation}
        search={search}
        validationError={validationError}
        disabled={loading && !hasData}
        onPresetChange={setPreset}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        onSituationChange={setSituation}
        onSearchChange={setSearch}
      />

      {showInitialLoading ? (
        <CommercialLoadingCard title="Carregando faturamento…" variant="panel" />
      ) : null}

      {error && !hasData ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <CommercialActionButton variant="ghost" onClick={reload}>
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {error && hasData ? (
        <CommercialStateBanner>
          <p>Não foi possível atualizar o faturamento: {error}</p>
          <CommercialActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing}
          >
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {data && !showInitialLoading ? (
        <>
          <CustomerBillingSummaryCards summary={data.summary} loading={refreshing} />
          {empty ? (
            <CommercialEmptyState
              title="Nenhuma nota fiscal encontrada"
              message="Ajuste o período ou os filtros para tentar novamente."
            />
          ) : (
            <CustomerInvoicesTable
              invoices={data.invoices}
              page={page}
              totalPages={data.pagination.total_pages}
              total={data.pagination.total}
              onPageChange={setPage}
              basePath={basePath}
              codigo={codigo}
              loja={loja}
            />
          )}
        </>
      ) : null}
    </div>
  );
}
