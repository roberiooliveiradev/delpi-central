import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { CommercialTitleWithHelp } from "../../../app/commercialUi";
import { Pagination } from "../../../components/Pagination";
import { CM_HELP } from "../../../content/helpTooltips";
import { EmptyState } from "../../../ui/EmptyState";
import { CustomerSummaryCards } from "../components/CustomerSummaryCards";
import { CustomerBillingSeriesChart } from "../components/CustomerBillingSeriesChart";
import { CustomersFilters } from "../components/CustomersFilters";
import { CustomersTable } from "../components/CustomersTable";
import { SellerScopeFilter } from "../components/SellerScopeFilter";
import { useCustomersData } from "../hooks/useCustomersData";
import { buildSellerNameByCustomerKey } from "../utils/sellerNameByCustomer";
import {
  buildCustomersListPath,
  buildCustomersListSearch,
  parseCustomersListDeepLink,
  type CustomersListSellerAccess,
} from "../../../utils/customersListDeepLink";

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
  const [hydratedSellerAccessKey, setHydratedSellerAccessKey] = useState<string | null>(null);

  const sellerAccess = useMemo<CustomersListSellerAccess>(
    () => ({
      allowSellerId: canUseTeamScope,
      validSellerIds: canUseTeamScope ? sellers.map((seller) => seller.id) : [],
    }),
    [canUseTeamScope, sellers],
  );
  const sellerAccessKey = `${sellerAccess.allowSellerId ? "team" : "own"}:${sellerAccess.validSellerIds.join(",")}`;

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
    setPage,
    search,
    setSearch,
    filter,
    setFilter,
    sortKey,
    sortDirection,
    toggleSort,
    resetFilters,
    lastSuccessAt,
    reload,
    portfolioMessage,
    portfolioEmpty,
  } = useCustomersData(canUseTeamScope ? sellerIdFilter : null, { sellerNameByKey });

  useEffect(() => {
    if (scopeLoading || typeof window === "undefined") return;

    const applyBrowserState = () => {
      const deepLink = parseCustomersListDeepLink(window.location.search, sellerAccess);
      setSearch(deepLink.q);
      setFilter(deepLink.focus);
      setSellerIdFilter(deepLink.sellerId);

      const canonicalPath = buildCustomersListPath(basePath, deepLink, sellerAccess);
      const currentPath = `${window.location.pathname}${window.location.search}`;
      if (canonicalPath !== currentPath) {
        window.history.replaceState(window.history.state, "", canonicalPath);
      }
    };

    applyBrowserState();
    setHydratedSellerAccessKey(sellerAccessKey);
    window.addEventListener("popstate", applyBrowserState);
    return () => window.removeEventListener("popstate", applyBrowserState);
  }, [
    basePath,
    scopeLoading,
    sellerAccess,
    sellerAccessKey,
    setFilter,
    setSearch,
    setSellerIdFilter,
  ]);

  const listSearch = useMemo(
    () =>
      buildCustomersListSearch(
        {
          q: search,
          focus: filter,
          sellerId: canUseTeamScope ? sellerIdFilter : null,
        },
        sellerAccess,
      ),
    [canUseTeamScope, filter, search, sellerAccess, sellerIdFilter],
  );

  useEffect(() => {
    if (
      scopeLoading ||
      typeof window === "undefined" ||
      hydratedSellerAccessKey !== sellerAccessKey
    ) {
      return;
    }
    const target = buildCustomersListPath(
      basePath,
      {
        q: search,
        focus: filter,
        sellerId: canUseTeamScope ? sellerIdFilter : null,
      },
      sellerAccess,
    );
    const current = `${window.location.pathname}${window.location.search}`;
    if (target !== current) {
      window.history.replaceState(window.history.state, "", target);
    }
  }, [
    basePath,
    canUseTeamScope,
    filter,
    hydratedSellerAccessKey,
    listSearch,
    search,
    sellerAccess,
    sellerIdFilter,
    scopeLoading,
    sellerAccessKey,
  ]);

  const hasActiveFilters = Boolean(search.trim()) || filter !== "all";
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

  return (
    <div className="pva-internal-page pva-customers-page">
      <header className="pva-customers-page__header">
        <div className="pva-customers-page__titles">
          <h2 className="pva-internal-page__title">
            <CommercialTitleWithHelp
              title="Minha carteira de clientes"
              hint={CM_HELP.customers.page}
            />
          </h2>
          <p className="pva-internal-page__text">
            Clientes da sua carteira com pedidos de venda em aberto — priorize atrasos e abra o
            detalhe do cliente.
          </p>
          <p className="pva-customers-page__updated" aria-live="polite">
            Atualizado em: {formatUpdatedAt(lastSuccessAt)}
            {refreshing ? " · Atualizando…" : ""}
          </p>
        </div>
        <div className="pva-customers-page__header-actions">
          {canUseTeamScope ? (
            <SellerScopeFilter
              sellers={sellers}
              value={sellerIdFilter}
              onChange={setSellerIdFilter}
            />
          ) : null}
          <button
            type="button"
            className="pva-btn pva-btn--secondary"
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
          </button>
        </div>
      </header>

      {portfolioEmpty && portfolioMessage ? (
        <EmptyState title="Carteira vazia" description={portfolioMessage} />
      ) : null}

      {showInitialLoading ? (
        <div
          className="pva-metrics pva-metrics--portfolio"
          aria-busy="true"
          role="status"
          aria-label="Carregando clientes"
        >
          <span className="visually-hidden">Carregando clientes…</span>
          {Array.from({ length: 5 }, (_, index) => (
            <div
              key={index}
              className={
                index === 2
                  ? "pva-card pva-kpi-card delpi-ui-card delpi-ui-kpi-card delpi-ui-kpi-card--wide"
                  : "pva-card pva-kpi-card delpi-ui-card delpi-ui-kpi-card"
              }
            >
              <div className="pva-skeleton" style={{ height: 14, width: "50%" }} />
              <div
                className="pva-skeleton"
                style={{ height: index === 2 ? 40 : 32, width: "60%", marginTop: 12 }}
              />
            </div>
          ))}
        </div>
      ) : null}

      {error && !hasData ? (
        <div className="pva-alert pva-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="pva-btn pva-btn--secondary" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {error && hasData ? (
        <div className="pva-alert pva-alert--warning" role="alert">
          <p>Não foi possível atualizar os dados: {error}</p>
          <button
            type="button"
            className="pva-btn pva-btn--secondary"
            onClick={reload}
            disabled={refreshing}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {aggregation && hasData && !showInitialLoading && !portfolioEmpty ? (
        <>
          <CustomerSummaryCards aggregation={aggregation} loading={refreshing} />

          <CustomerBillingSeriesChart customers={aggregation.customers} />

          {aggregation.incompleteLineCount > 0 ? (
            <div className="pva-alert pva-alert--warning" role="status">
              <p>
                {aggregation.incompleteLineCount.toLocaleString("pt-BR")} linha(s) de pedido não
                foram agrupadas por ausência de identificação cadastral (código e/ou loja).
                Essas linhas continuam disponíveis em Pedidos em aberto.
              </p>
            </div>
          ) : null}

          <CustomersFilters
            search={search}
            filter={filter}
            onSearchChange={setSearch}
            onFilterChange={setFilter}
            onReset={resetFilters}
            hasActiveFilters={hasActiveFilters}
          />

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
                <button type="button" className="pva-btn pva-btn--secondary" onClick={resetFilters}>
                  Limpar busca e filtros
                </button>
              }
            />
          ) : null}

          {!showEmptyDataset && !showFilteredEmpty ? (
            <section className="pva-section" aria-label="Todos os clientes da carteira">
              <div className="pva-section__header">
                <div>
                  <h2 className="pva-customers-page__list-title">
                    Clientes da carteira
                    <HelpTooltip
                      content={CM_HELP.customers.list}
                      ariaLabel="Ajuda: Clientes da carteira"
                      placement="bottom"
                    />
                  </h2>
                  <p className="pva-section__hint">
                    {filteredCustomers.length === 0
                      ? "0 clientes"
                      : `${((page - 1) * 20 + 1).toLocaleString("pt-BR")}–${Math.min(page * 20, filteredCustomers.length).toLocaleString("pt-BR")} de ${filteredCustomers.length.toLocaleString("pt-BR")} clientes`}
                  </p>
                </div>
              </div>
              <CustomersTable
                customers={pagedCustomers}
                sortKey={sortKey}
                sortDirection={sortDirection}
                onSort={toggleSort}
                basePath={basePath}
                listSearch={listSearch}
                sellerAccess={sellerAccess}
              />
              {filteredCustomers.length > 20 ? (
                <Pagination
                  page={page}
                  pageSize={20}
                  total={filteredCustomers.length}
                  onPageChange={setPage}
                />
              ) : null}
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
