import { RefreshCw } from "lucide-react";
import { useEffect, useMemo } from "react";

import { usePortfolioScope } from "../../../app/usePortfolioScope";
import {
  CommercialActionButton,
  CommercialFilterBarShell,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialStateBanner,
  CommercialTextField,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { EmptyState } from "../../../ui/EmptyState";
import { CustomerSummaryCards } from "../components/CustomerSummaryCards";
import { CustomerBillingSeriesChart } from "../components/CustomerBillingSeriesChart";
import { CustomersTable } from "../components/CustomersTable";
import { SellerScopeFilter } from "../components/SellerScopeFilter";
import { useCustomersData } from "../hooks/useCustomersData";
import { useCustomersListState } from "../hooks/useCustomersListState";
import type { CustomerAttentionFilter } from "../types/customerSummary";
import { matchesCustomerFilter } from "../utils/customerFilters";
import { buildSellerNameByCustomerKey } from "../utils/sellerNameByCustomer";
import type { CustomersListSellerAccess } from "../../../utils/customersListDeepLink";

function formatUpdatedAt(value: Date | null): string {
  if (!value) return "—";
  return value.toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

type CustomersPageProps = {
  basePath: string;
};

/**
 * Minha carteira — clientes com pedidos em aberto no escopo do vendedor.
 */
export function CustomersPage({ basePath }: CustomersPageProps) {
  const {
    loading: scopeLoading,
    canUseTeamScope,
    sellers,
    sellerIdFilter,
    setSellerIdFilter,
    myPortfolio,
  } = usePortfolioScope();
  const sellerAccess = useMemo<CustomersListSellerAccess>(
    () => ({
      allowSellerId: canUseTeamScope,
      validSellerIds: canUseTeamScope ? sellers.map((seller) => seller.id) : [],
    }),
    [canUseTeamScope, sellers],
  );
  const sellerAccessKey = `${sellerAccess.allowSellerId ? "team" : "own"}:${sellerAccess.validSellerIds.join(",")}`;
  const {
    state: listState,
    setSearch,
    setFilter,
    setSellerId,
    toggleSort,
    setPage,
    resetFilters,
    listSearch,
  } = useCustomersListState({
    basePath,
    scopeLoading,
    sellerAccess,
    sellerAccessKey,
    sellerId: canUseTeamScope ? sellerIdFilter : null,
    setSellerId: setSellerIdFilter,
  });

  const sellerNameByKey = useMemo(() => {
    if (canUseTeamScope) {
      return buildSellerNameByCustomerKey(sellers);
    }
    if (myPortfolio) {
      return buildSellerNameByCustomerKey([myPortfolio]);
    }
    return new Map<string, string>();
  }, [canUseTeamScope, sellers, myPortfolio]);

  const {
    loading,
    refreshing,
    error,
    hasData,
    aggregation,
    filteredCustomers,
    pagedCustomers,
    page,
    lastSuccessAt,
    reload,
    portfolioMessage,
    portfolioEmpty,
    enrichment,
  } = useCustomersData(canUseTeamScope ? sellerIdFilter : null, {
    sellerNameByKey,
    listState,
  });
  const {
    q: search,
    focus: filter,
    sort: sortKey,
    dir: sortDirection,
    page: requestedPage,
  } = listState;
  const enrichmentIncomplete =
    !enrichment.loading &&
    enrichment.total > 0 &&
    (enrichment.covered < enrichment.total ||
      enrichment.failedBatches > 0 ||
      Boolean(enrichment.error));
  useEffect(() => {
    if (aggregation && requestedPage !== page) setPage(page);
  }, [aggregation, page, requestedPage, setPage]);
  useEffect(() => {
    if (enrichmentIncomplete && filter === "no_sale_60") setFilter("all");
  }, [enrichmentIncomplete, filter, setFilter]);
  const hasActiveFilters =
    Boolean(search.trim()) || filter !== "all" || listState.sellerId !== null;
  const showInitialLoading = loading && !hasData;
  const showEmptyDataset =
    !loading &&
    !error &&
    aggregation !== null &&
    aggregation.customers.length === 0;
  const showFilteredEmpty =
    !loading &&
    aggregation !== null &&
    aggregation.customers.length > 0 &&
    filteredCustomers.length === 0;
  const focusOptions: Array<{ id: CustomerAttentionFilter; label: string }> = [
    { id: "all", label: "Todos" },
    { id: "attention", label: "Atenção" },
    { id: "inactive", label: "Inativos" },
    { id: "growth", label: "Em crescimento" },
    { id: "no_sale_60", label: "Sem venda 60d" },
  ];
  const focusChips = focusOptions.map((option) => ({
    id: option.id,
    label: `${option.label} (${(aggregation?.customers.filter((customer) => matchesCustomerFilter(customer, option.id)).length ?? 0).toLocaleString("pt-BR")})${option.id === "no_sale_60" && enrichmentIncomplete ? " · indisponível" : ""}`,
    active: filter === option.id,
    onSelect: option.id === "no_sale_60" && enrichmentIncomplete
      ? undefined
      : () => setFilter(option.id),
  }));
  const highlights = [
    {
      id: "customers",
      label: "Clientes no recorte",
      value: (aggregation?.customers.length ?? 0).toLocaleString("pt-BR"),
    },
    {
      id: "open-value",
      label: "Valor em aberto",
      value: aggregation
        ? aggregation.totalValorAberto.toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
          })
        : "—",
    },
    {
      id: "filtered",
      label: "Após filtros",
      value: filteredCustomers.length.toLocaleString("pt-BR"),
    },
  ];

  return (
    <section className="cm-page-stack cm-customers-page">
      <CommercialPageHero
        aria-label="Minha carteira"
        eyebrow="Carteira"
        title={
          <CommercialSectionHintLabel
            label="Minha carteira"
            hint={CM_HELP.customers.page}
          />
        }
        description="Clientes da carteira com pedidos de venda em aberto — priorize o atendimento e abra a Conta."
        highlights={highlights}
        actions={
          <div className="cm-customers-page__actions">
            <span className="cm-customers-page__freshness" aria-live="polite">
              Atualizado em {formatUpdatedAt(lastSuccessAt)}
              {refreshing ? " · Atualizando…" : ""}
            </span>
            <CommercialActionButton
              variant="ghost"
              onClick={reload}
              disabled={loading || refreshing}
              aria-busy={refreshing || loading}
            >
              <RefreshCw
                size={16}
                aria-hidden="true"
                className={refreshing ? "pva-spin" : undefined}
              />
              {refreshing || loading ? "Atualizando…" : "Atualizar"}
            </CommercialActionButton>
          </div>
        }
      >
        <CommercialScopeChipBar
          label="Foco"
          aria-label="Foco da carteira"
          chips={focusChips}
        />
        <CommercialFilterBarShell embedded ariaLabel="Busca e escopo da carteira">
          <CommercialTextField
            label="Buscar cliente"
            hint={CM_HELP.customers.filterSearch}
            type="search"
            value={search}
            onChange={setSearch}
            placeholder="Código, loja, nome ou pedido"
          />
          {canUseTeamScope ? (
            <SellerScopeFilter
              sellers={sellers}
              value={sellerIdFilter}
              onChange={setSellerId}
              hint={CM_HELP.customers.sellerScope}
            />
          ) : null}
          {hasActiveFilters ? (
            <div className="cm-customers-page__filter-actions">
              <CommercialActionButton variant="ghost" onClick={resetFilters}>
                Limpar filtros
              </CommercialActionButton>
            </div>
          ) : null}
        </CommercialFilterBarShell>
      </CommercialPageHero>

      {portfolioEmpty && portfolioMessage ? (
        <EmptyState title="Carteira vazia" description={portfolioMessage} />
      ) : null}

      {showInitialLoading ? (
        <CommercialLoadingCard title="Carregando clientes…" variant="panel" />
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
          <p>Não foi possível atualizar os dados: {error}</p>
          <CommercialActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing}
          >
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {enrichment.error ? (
        <CommercialStateBanner>
          <p>
            Cadastro e faturamento com cobertura parcial
            {enrichment.total > 0
              ? ` (${enrichment.covered}/${enrichment.total}; ${enrichment.failedBatches} lote(s) com falha)`
              : ""}
            : {enrichment.error}
          </p>
        </CommercialStateBanner>
      ) : null}

      {enrichment.lastSuccessAt ? (
        <p className="cm-customers-page__freshness" aria-live="polite">
          Enrichment atualizado em {formatUpdatedAt(enrichment.lastSuccessAt)}
        </p>
      ) : null}

      {aggregation && hasData && !showInitialLoading && !portfolioEmpty ? (
        <>
          <CustomerSummaryCards aggregation={aggregation} loading={refreshing} />

          {aggregation.incompleteLineCount > 0 ? (
            <CommercialStateBanner>
              <p>
                {aggregation.incompleteLineCount.toLocaleString("pt-BR")} linha(s) de pedido não
                foram agrupadas por ausência de identificação cadastral (código e/ou loja).
                Essas linhas continuam disponíveis em Pedidos em aberto.
              </p>
            </CommercialStateBanner>
          ) : null}

          {showEmptyDataset ? (
            <EmptyState
              title="Nenhum cliente em aberto"
              description="Não há pedidos de venda em aberto para os clientes da carteira no momento."
            />
          ) : null}

          {showFilteredEmpty ? (
            <EmptyState
              title="Nenhum resultado"
              description="Nenhum cliente corresponde à busca e aos filtros."
              action={
                <CommercialActionButton variant="ghost" onClick={resetFilters}>
                  Limpar busca e filtros
                </CommercialActionButton>
              }
            />
          ) : null}

          {!showEmptyDataset && !showFilteredEmpty ? (
            <CommercialSectionCard
              title="Clientes da carteira"
              subtitle={
                filteredCustomers.length === 0
                  ? "0 clientes"
                  : `${((page - 1) * 20 + 1).toLocaleString("pt-BR")}–${Math.min(page * 20, filteredCustomers.length).toLocaleString("pt-BR")} de ${filteredCustomers.length.toLocaleString("pt-BR")} clientes`
              }
              hint={CM_HELP.customers.list}
            >
              <CustomersTable
                customers={pagedCustomers}
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSort={toggleSort}
                basePath={basePath}
                listSearch={listSearch}
                sellerAccess={sellerAccess}
                loading={refreshing}
              />
              {filteredCustomers.length > 20 ? (
                <CommercialPagination
                  page={page}
                  pageSize={20}
                  total={filteredCustomers.length}
                  onPageChange={setPage}
                />
              ) : null}
            </CommercialSectionCard>
          ) : null}

          <CustomerBillingSeriesChart customers={aggregation.customers} />
        </>
      ) : null}
    </section>
  );
}
