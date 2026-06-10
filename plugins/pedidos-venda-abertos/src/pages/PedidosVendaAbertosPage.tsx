import {
  AlertTriangle,
  CalendarClock,
  Package,
  PackageCheck,
  Wallet,
} from "lucide-react";

import { FilterBar } from "../components/FilterBar";
import { KpiCard } from "../components/KpiCard";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { PedidosTable } from "../components/PedidosTable";
import { usePedidosVendaAbertosDashboard } from "../hooks/usePedidosVendaAbertosDashboard";
import { formatCurrency } from "../utils/format";

export function PedidosVendaAbertosPage() {
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
  } = usePedidosVendaAbertosDashboard();

  const showEmptyDataset = !loading && !error && allItemsCount === 0;
  const showFilteredEmpty =
    !loading && !error && allItemsCount > 0 && totalFiltered === 0;

  return (
    <div className="dashboard-pedidos-venda-abertos dashboard-page">
      <div className="pva-app-shell">
        <PageHeader loading={loading} onRefresh={reload} totalLoaded={allItemsCount} />

        {loading && !allItemsCount ? (
          <div className="pva-state-box" role="status">
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
          <div className="pva-state-box">Nenhum pedido em aberto encontrado.</div>
        ) : null}

        {!error && allItemsCount > 0 ? (
          <>
            <section className="pva-kpi-grid" aria-label="Resumo">
              <KpiCard
                title="Linhas em aberto"
                value={summary.total_linhas.toLocaleString("pt-BR")}
                subtitle={hasActiveFilters ? "Com filtros aplicados" : "Total carregado"}
                icon={<Package size={22} />}
                loading={loading}
              />
              <KpiCard
                title="Valor em aberto"
                value={formatCurrency(summary.valor_total_aberto)}
                icon={<Wallet size={22} />}
                loading={loading}
                wide
              />
              <KpiCard
                title="Pode faturar"
                value={summary.itens_com_estoque.toLocaleString("pt-BR")}
                icon={<PackageCheck size={22} />}
                loading={loading}
              />
              <KpiCard
                title="Estoque parcial"
                value={summary.itens_estoque_parcial.toLocaleString("pt-BR")}
                icon={<AlertTriangle size={22} />}
                loading={loading}
              />
              <KpiCard
                title="Pedidos em atraso"
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

            <PedidosTable
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
      </div>
    </div>
  );
}
