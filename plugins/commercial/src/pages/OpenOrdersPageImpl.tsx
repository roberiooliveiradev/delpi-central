import { useEffect } from "react";
import {
  AlertTriangle,
  CalendarClock,
  Package,
  PackageCheck,
  Wallet,
} from "lucide-react";

import { PVA_STATE_BOX } from "../ui/stateChrome";
import { usePortfolioScope } from "../app/usePortfolioScope";
import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { OpenOrdersTable } from "../components/OpenOrdersTable";
import { CM_HELP } from "../content/helpTooltips";
import { SellerScopeFilter } from "../features/customers/components/SellerScopeFilter";
import { useOpenOrdersDashboard } from "../hooks/useOpenOrdersDashboard";
import { EmptyState } from "../ui/EmptyState";
import { formatCurrency } from "../utils/format";

export function OpenOrdersPageImpl() {
  const {
    canUseTeamScope,
    sellers,
    sellerIdFilter,
    setSellerIdFilter,
  } = usePortfolioScope();

  // Deep link da Gestão Equipe: ?seller_id=
  useEffect(() => {
    if (!canUseTeamScope || typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search || "");
    const fromQuery = (params.get("seller_id") || "").trim();
    if (fromQuery && fromQuery !== (sellerIdFilter || "")) {
      setSellerIdFilter(fromQuery);
    }
  }, [canUseTeamScope, sellerIdFilter, setSellerIdFilter]);

  const {
    loading,
    error,
    opsWarning,
    reload,
    allItemsCount,
    paginatedItems,
    summary,
    filters,
    updateFilters,
    resetFilters,
    hasActiveFilters,
    filiais,
    clients,
    page,
    pageSize,
    totalFiltered,
    sortedItems,
    setPage,
    sortKey,
    sortDirection,
    toggleSort,
  } = useOpenOrdersDashboard(canUseTeamScope ? sellerIdFilter : null);

  const showEmptyDataset = !loading && !error && allItemsCount === 0;
  const showFilteredEmpty =
    !loading && !error && allItemsCount > 0 && totalFiltered === 0;

  return (
    <>
      <PageHeader loading={loading} onRefresh={reload} totalLoaded={allItemsCount} />

      {canUseTeamScope ? (
        <div className="pva-customers-page__header" style={{ marginBottom: 8 }}>
          <SellerScopeFilter
            sellers={sellers}
            value={sellerIdFilter}
            onChange={setSellerIdFilter}
          />
        </div>
      ) : null}

      {loading && !allItemsCount ? (
        <div className={PVA_STATE_BOX} role="status">
          Carregando pedidos em aberto…
        </div>
      ) : null}

      {!loading && error ? (
        <div className="pva-alert pva-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="pva-btn pva-btn--ghost" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {showEmptyDataset ? (
        <EmptyState
          title="Nenhum pedido em aberto"
          description="Não há linhas em aberto no escopo da carteira selecionada."
        />
      ) : null}

      {!error && allItemsCount > 0 ? (
        <>
          <section className="pva-kpi-grid" aria-label="Resumo">
            <KpiCard
              title="Linhas em aberto"
              titleHint={CM_HELP.openOrders.kpiLines}
              value={summary.total_linhas.toLocaleString("pt-BR")}
              subtitle={hasActiveFilters ? "Com filtros aplicados" : "Total carregado"}
              icon={<Package size={22} />}
              loading={loading}
            />
            <KpiCard
              title="Valor em aberto"
              titleHint={CM_HELP.openOrders.kpiValue}
              value={formatCurrency(summary.valor_total_aberto)}
              icon={<Wallet size={22} />}
              loading={loading}
              wide
            />
            <KpiCard
              title="Pode faturar"
              titleHint={CM_HELP.openOrders.kpiCanInvoice}
              value={summary.itens_com_estoque.toLocaleString("pt-BR")}
              icon={<PackageCheck size={22} />}
              loading={loading}
            />
            <KpiCard
              title="Estoque parcial"
              titleHint={CM_HELP.openOrders.kpiPartialStock}
              value={summary.itens_estoque_parcial.toLocaleString("pt-BR")}
              icon={<AlertTriangle size={22} />}
              loading={loading}
            />
            <KpiCard
              title="Pedidos em atraso"
              titleHint={CM_HELP.openOrders.kpiLate}
              value={summary.linhas_em_atraso.toLocaleString("pt-BR")}
              icon={<CalendarClock size={22} />}
              loading={loading}
              valueTone={summary.linhas_em_atraso > 0 ? "danger" : "default"}
            />
          </section>

          <FilterBar
            filters={filters}
            filiais={filiais}
            clients={clients}
            hasActiveFilters={hasActiveFilters}
            onChange={updateFilters}
            onReset={resetFilters}
          />

          {opsWarning ? (
            <div className="pva-alert pva-alert--warning" role="status">
              <p>
                Pedidos carregados, mas a previsão produtiva (OPs abertas) não está disponível:{" "}
                {opsWarning}
              </p>
            </div>
          ) : null}

          <OpenOrdersTable
            rows={paginatedItems}
            exportRows={sortedItems}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSort={toggleSort}
            loading={loading}
            emptyMessage={
              showFilteredEmpty
                ? "Nenhum pedido corresponde aos filtros selecionados."
                : "Nenhum registro encontrado."
            }
          />

          <Pagination
            page={page}
            pageSize={pageSize}
            total={totalFiltered}
            onPageChange={setPage}
          />
        </>
      ) : null}
    </>
  );
}
