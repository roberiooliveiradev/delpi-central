import { useCallback } from "react";
import { EmptyState, SectionHintLabel } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";

import {
  CommercialActionButton,
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
type ConcentrateChipId = "none" | "overdue" | "current_month" | "future";

function resolveAttentionChip(filters: {
  stockStatus: StockFilter;
  lateOnly: boolean;
}): AttentionChipId {
  if (filters.lateOnly) return "late";
  if (filters.stockStatus === "com_estoque") return "can_invoice";
  if (filters.stockStatus === "parcial") return "partial";
  return "all";
}

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

function monthBoundsFromAsOf(asOfIso: string | undefined): {
  y: number;
  m: number;
  currentStart: string;
  currentEnd: string;
  futureStart: string;
} {
  const day = (asOfIso ?? "").slice(0, 10);
  const today = /^\d{4}-\d{2}-\d{2}$/.test(day)
    ? day
    : new Date().toISOString().slice(0, 10);
  const [y, m] = today.split("-").map(Number);
  const last = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const nextIdx = y * 12 + m;
  const fy = Math.floor(nextIdx / 12);
  const fm = (nextIdx % 12) + 1;
  return {
    y,
    m,
    currentStart: `${y}-${pad2(m)}-01`,
    currentEnd: `${y}-${pad2(m)}-${pad2(last)}`,
    futureStart: `${fy}-${pad2(fm)}-01`,
  };
}

function resolveConcentrateChip(filters: {
  lateOnly: boolean;
  dateStart: string;
  dateEnd: string;
  asOfIso?: string;
}): ConcentrateChipId {
  if (filters.lateOnly && !filters.dateStart && !filters.dateEnd) return "overdue";
  const bounds = monthBoundsFromAsOf(filters.asOfIso);
  if (filters.dateStart === bounds.currentStart && filters.dateEnd === bounds.currentEnd) {
    return "current_month";
  }
  if (filters.dateStart === bounds.futureStart && !filters.dateEnd && !filters.lateOnly) {
    return "future";
  }
  return "none";
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
    deliveryHorizon,
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
  const concentrateChip = resolveConcentrateChip({
    lateOnly: filters.lateOnly,
    dateStart: filters.dateStart,
    dateEnd: filters.dateEnd,
    asOfIso: deliveryHorizon?.asOf,
  });

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
    updateFilters({ stockStatus: "", lateOnly: true, dateStart: "", dateEnd: "" });
  };

  const selectConcentrate = (id: ConcentrateChipId) => {
    const bounds = monthBoundsFromAsOf(deliveryHorizon?.asOf);
    if (id === "none") {
      updateFilters({ lateOnly: false, dateStart: "", dateEnd: "", stockStatus: "" as StockFilter });
      return;
    }
    if (id === "overdue") {
      updateFilters({
        lateOnly: true,
        dateStart: "",
        dateEnd: "",
        stockStatus: "" as StockFilter,
      });
      return;
    }
    if (id === "current_month") {
      updateFilters({
        lateOnly: false,
        dateStart: bounds.currentStart,
        dateEnd: bounds.currentEnd,
        stockStatus: "" as StockFilter,
      });
      return;
    }
    updateFilters({
      lateOnly: false,
      dateStart: bounds.futureStart,
      dateEnd: "",
      stockStatus: "" as StockFilter,
    });
  };

  const horizonCount = (id: string) => {
    const bucket = deliveryHorizon?.buckets?.find((b) => b.id === id);
    return bucket?.openLineCount ?? 0;
  };
  const futureCount =
    horizonCount("next_1_3_months") + horizonCount("later");

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
            <CommercialActionButton variant="ghost" onClick={() => reload()} disabled={loading}>
              <RefreshCw size={16} aria-hidden="true" />
              <span>Atualizar</span>
            </CommercialActionButton>
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

            {deliveryHorizon ? (
              <CommercialScopeChipBar
                aria-label="Concentrar forças por entrega"
                label="Concentrar"
                chips={[
                  {
                    id: "conc-none",
                    label: "Todos",
                    active: concentrateChip === "none",
                    onSelect: () => selectConcentrate("none"),
                  },
                  {
                    id: "conc-overdue",
                    label: `Atrasado (${horizonCount("overdue").toLocaleString("pt-BR")})`,
                    active: concentrateChip === "overdue",
                    onSelect: () => selectConcentrate("overdue"),
                  },
                  {
                    id: "conc-month",
                    label: `Este mês (${horizonCount("current_month").toLocaleString("pt-BR")})`,
                    active: concentrateChip === "current_month",
                    onSelect: () => selectConcentrate("current_month"),
                  },
                  {
                    id: "conc-future",
                    label: `Futuro (${futureCount.toLocaleString("pt-BR")})`,
                    active: concentrateChip === "future",
                    onSelect: () => selectConcentrate("future"),
                  },
                ]}
              />
            ) : null}

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
          <CommercialActionButton variant="ghost" onClick={() => reload()}>
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {portfolioEmpty ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={
            portfolioMessage ||
            (canOpenSellerPortfolios
              ? "Carteira sem clientes. Inclua clientes em Administração para ver pedidos em aberto."
              : "Sua carteira ainda não possui clientes vinculados. Peça ao gerente para incluir clientes.")
          }
        >
          {canOpenSellerPortfolios ? (
            <CommercialActionButton
              variant="primary"
              onClick={() => navigatePluginView("administration")}
            >
              Abrir Administração
            </CommercialActionButton>
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
            sellerId={canFilterPortfolios ? sellerIdFilter : null}
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
