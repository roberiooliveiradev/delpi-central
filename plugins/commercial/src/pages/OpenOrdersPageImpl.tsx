import { useCallback } from "react";
import { ActionButton, EmptyState, SectionHintLabel } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";

import {
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialScopeChipBar,
  CommercialStateBanner,
  cmEmptyStateClassNames,
} from "../app/commercialUi";
import { navigatePluginView } from "../app/pluginNavigation";
import { usePortfolioScope } from "../app/usePortfolioScope";
import { usePortfolioSellerAccess } from "../app/usePortfolioSellerAccess";
import { FilterBar } from "../components/FilterBar";
import { OpenOrdersTable } from "../components/OpenOrdersTable";
import { CM_HELP } from "../content/helpTooltips";
import { SellerScopeFilter } from "../features/customers/components/SellerScopeFilter";
import { useOpenOrdersDashboard } from "../hooks/useOpenOrdersDashboard";
import { formatCurrency } from "../utils/format";
import type { StockFilter } from "../utils/statusBadges";

type AttentionChipId = "all" | "can_invoice" | "partial" | "late";

function resolveAttentionChip(filters: {
  stockStatus: StockFilter;
  lateOnly: boolean;
}): AttentionChipId {
  if (filters.lateOnly) return "late";
  if (filters.stockStatus === "com_estoque") return "can_invoice";
  if (filters.stockStatus === "parcial") return "partial";
  return "all";
}

function formatUpdatedAt(value: Date): string {
  return value.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function OpenOrdersPageImpl({ basePath }: { basePath?: string }) {
  const {
    loading: sellerScopeLoading,
    canFilterPortfolios,
    canUseTeamScope,
    canManagePortfolios,
    isAdmin,
    filterablePortfolios,
    sellerIdFilter,
    setSellerIdFilter,
  } = usePortfolioScope();

  const canOpenSellerPortfolios = canManagePortfolios || isAdmin;

  const sellerAccess = usePortfolioSellerAccess();
  const restoreSellerFromUrl = useCallback(
    (sellerId: string | null) => setSellerIdFilter(sellerId),
    [setSellerIdFilter],
  );

  const {
    loading,
    error,
    opsWarning,
    reload,
    lastUpdatedAt,
    portfolioEmpty,
    portfolioMessage,
    allItemsCount,
    paginatedItems,
    summary,
    attentionSummary,
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
  } = useOpenOrdersDashboard(canFilterPortfolios ? sellerIdFilter : null, {
    basePath,
    sellerAccess,
    sellerScopeLoading,
    onSellerIdChange: restoreSellerFromUrl,
  });

  const changeSeller = (sellerId: string | null) => {
    setSellerIdFilter(sellerId);
    setPage(1);
  };

  const showEmptyDataset = !loading && !error && allItemsCount === 0 && !portfolioEmpty;
  const showFilteredEmpty =
    !loading && !error && allItemsCount > 0 && totalFiltered === 0;
  const activeChip = resolveAttentionChip(filters);

  const selectChip = (id: AttentionChipId) => {
    if (id === "all") {
      updateFilters({ stockStatus: "" as StockFilter, lateOnly: false });
      return;
    }
    if (id === "can_invoice") {
      updateFilters({ stockStatus: "com_estoque", lateOnly: false });
      return;
    }
    if (id === "partial") {
      updateFilters({ stockStatus: "parcial", lateOnly: false });
      return;
    }
    updateFilters({ stockStatus: "", lateOnly: true });
  };

  const highlights = [
    {
      id: "linhas",
      label: "Linhas",
      value: loading && !allItemsCount ? "—" : allItemsCount.toLocaleString("pt-BR"),
    },
    {
      id: "valor",
      label: "Valor em aberto",
      value: loading && !allItemsCount ? "—" : formatCurrency(summary.valor_total_aberto),
    },
    ...(hasActiveFilters
      ? [
          {
            id: "filtradas",
            label: "Após filtros",
            value: totalFiltered.toLocaleString("pt-BR"),
          },
        ]
      : []),
  ];

  return (
    <section className="cm-page-stack cm-open-orders-page">
      <CommercialPageHero
        aria-label="Pedidos em aberto"
        eyebrow="Pedidos"
        title={
          <SectionHintLabel label="Pedidos em aberto" hint={CM_HELP.openOrders.page} />
        }
        actions={
          <div className="cm-open-orders-page__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span
                className="cm-open-orders-page__freshness"
                title={CM_HELP.openOrders.freshness}
              >
                Atualizado às {formatUpdatedAt(lastUpdatedAt)}
              </span>
            ) : null}
            <ActionButton variant="ghost" onClick={() => reload()} disabled={loading}>
              <RefreshCw size={16} aria-hidden="true" />
              <span>Atualizar</span>
            </ActionButton>
          </div>
        }
        highlights={highlights}
      >
        {canFilterPortfolios ? (
          <div className="cm-open-orders-page__scope">
            <SellerScopeFilter
              sellers={filterablePortfolios}
              value={sellerIdFilter}
              onChange={changeSeller}
              hint={CM_HELP.openOrders.sellerScope}
              teamScope={canUseTeamScope}
            />
          </div>
        ) : null}

        {!error && allItemsCount > 0 ? (
          <>
            <CommercialScopeChipBar
              aria-label="Atenção operacional"
              label="Atenção"
              chips={[
                {
                  id: "all",
                  label: `Todos (${attentionSummary.total_linhas.toLocaleString("pt-BR")})`,
                  active: activeChip === "all",
                  onSelect: () => selectChip("all"),
                },
                {
                  id: "can_invoice",
                  label: `Pode faturar (${attentionSummary.itens_com_estoque.toLocaleString("pt-BR")})`,
                  active: activeChip === "can_invoice",
                  onSelect: () => selectChip("can_invoice"),
                },
                {
                  id: "partial",
                  label: `Parcial (${attentionSummary.itens_estoque_parcial.toLocaleString("pt-BR")})`,
                  active: activeChip === "partial",
                  onSelect: () => selectChip("partial"),
                },
                {
                  id: "late",
                  label: `Atraso (${attentionSummary.linhas_em_atraso.toLocaleString("pt-BR")})`,
                  active: activeChip === "late",
                  onSelect: () => selectChip("late"),
                },
              ]}
            />

            <FilterBar
              filters={filters}
              filiais={filiais}
              clients={clients}
              hasActiveFilters={hasActiveFilters}
              onChange={updateFilters}
              onReset={resetFilters}
            />
          </>
        ) : null}
      </CommercialPageHero>

      {loading && !allItemsCount && !portfolioEmpty ? (
        <CommercialLoadingCard title="Carregando pedidos em aberto…" variant="panel" />
      ) : null}

      {!loading && error ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <ActionButton variant="ghost" onClick={() => reload()}>
            Tentar novamente
          </ActionButton>
        </CommercialStateBanner>
      ) : null}

      {portfolioEmpty ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={
            portfolioMessage ||
            (canOpenSellerPortfolios
              ? "Carteira sem clientes. Inclua clientes em Carteiras para ver pedidos em aberto."
              : "Sua carteira ainda não possui clientes vinculados. Peça ao gerente para incluir clientes.")
          }
        >
          {canOpenSellerPortfolios ? (
            <ActionButton
              variant="primary"
              onClick={() => navigatePluginView("seller_portfolios")}
            >
              Abrir carteiras
            </ActionButton>
          ) : null}
        </EmptyState>
      ) : null}

      {showEmptyDataset ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultTitle="Nenhum pedido em aberto"
          defaultMessage="Não há linhas em aberto no escopo da carteira selecionada."
        />
      ) : null}

      {opsWarning && allItemsCount > 0 ? (
        <CommercialStateBanner>
          Pedidos carregados, mas a previsão produtiva (OPs abertas) não está disponível:{" "}
          {opsWarning}
        </CommercialStateBanner>
      ) : null}

      {!error && !portfolioEmpty && allItemsCount > 0 ? (
        <>
          <OpenOrdersTable
            basePath={basePath}
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

          <CommercialPagination
            page={page}
            pageSize={pageSize}
            total={totalFiltered}
            onPageChange={setPage}
          />
        </>
      ) : null}
    </section>
  );
}
