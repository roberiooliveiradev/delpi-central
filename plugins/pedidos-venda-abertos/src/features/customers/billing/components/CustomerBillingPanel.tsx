import { RefreshCw } from "lucide-react";

import { PVA_STATE_BOX } from "../../../../ui/stateChrome";
import type { UseCustomerBillingResult } from "../hooks/useCustomerBilling";
import { CustomerBillingFilters } from "./CustomerBillingFilters";
import { CustomerBillingSummaryCards } from "./CustomerBillingSummaryCards";
import { CustomerInvoicesTable } from "./CustomerInvoicesTable";

type CustomerBillingPanelProps = {
  billing: UseCustomerBillingResult;
};

export function CustomerBillingPanel({ billing }: CustomerBillingPanelProps) {
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
    <div className="pva-billing-panel">
      <header className="pva-checkup__nav-row">
        <h2 className="pva-checkup-section-title" style={{ margin: 0 }}>
          Faturamento e notas fiscais
        </h2>
        <button
          type="button"
          className="pva-btn pva-btn--ghost"
          onClick={reload}
          disabled={loading || refreshing || Boolean(validationError)}
          aria-busy={refreshing || loading}
        >
          <RefreshCw size={16} aria-hidden="true" className={refreshing ? "pva-spin" : undefined} />
          {refreshing || loading ? "Atualizando…" : "Atualizar"}
        </button>
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
        <div className={PVA_STATE_BOX} role="status">
          Carregando faturamento…
        </div>
      ) : null}

      {error && !hasData ? (
        <div className="pva-alert pva-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="pva-btn pva-btn--ghost" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {error && hasData ? (
        <div className="pva-alert pva-alert--warning" role="alert">
          <p>Não foi possível atualizar o faturamento: {error}</p>
          <button
            type="button"
            className="pva-btn pva-btn--ghost"
            onClick={reload}
            disabled={refreshing}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {data && !showInitialLoading ? (
        <>
          <CustomerBillingSummaryCards summary={data.summary} loading={refreshing} />
          {empty ? (
            <div className={PVA_STATE_BOX} role="status">
              Não foram encontradas notas fiscais de saída no período selecionado. Ajuste o
              período ou os filtros para tentar novamente.
            </div>
          ) : (
            <CustomerInvoicesTable
              invoices={data.invoices}
              page={page}
              totalPages={data.pagination.total_pages}
              total={data.pagination.total}
              onPageChange={setPage}
            />
          )}
        </>
      ) : null}
    </div>
  );
}
