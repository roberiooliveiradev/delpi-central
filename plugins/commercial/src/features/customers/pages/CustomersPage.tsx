import { RefreshCw, TriangleAlert } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { navigatePluginView } from "../../../app/pluginNavigation";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import {
  portfolioSellerAccessKey,
  usePortfolioSellerAccess,
} from "../../../app/usePortfolioSellerAccess";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialFilterBarShell,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialStateBanner,
  CommercialTextField,
  CommercialSegmentToggle,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { CustomerBillingSeriesChart } from "../components/CustomerBillingSeriesChart";
import { PortfolioBillingRankingTable } from "../components/PortfolioBillingRankingTable";
import { CustomersTable } from "../components/CustomersTable";
import { MyPortfolioAuditSection } from "../components/MyPortfolioAuditSection";
import { SellerScopeFilter } from "../components/SellerScopeFilter";
import { useCustomersData } from "../hooks/useCustomersData";
import { useCustomerSharedCoverage } from "../hooks/useCustomerSharedCoverage";
import { useCustomersListState } from "../hooks/useCustomersListState";
import { usePortfolioBillingShare } from "../hooks/usePortfolioBillingShare";
import type {
  CustomerAttentionFilter,
  CustomerTrendFilter,
} from "../types/customerSummary";
import {
  matchesBillingTrend,
  matchesOperationalFocus,
} from "../utils/customerFilters";
import { buildSellerNameByCustomerKey } from "../utils/sellerNameByCustomer";
import {
  BILLING_TREND_WINDOW_PRESETS,
  clampBillingTrendWindowDays,
  DEFAULT_BILLING_TREND_WINDOW_DAYS,
  type BillingTrendWindowPreset,
} from "../utils/billingTrendWindow";

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
    canFilterPortfolios,
    filterablePortfolios,
    sellers,
    sellerIdFilter,
    setSellerIdFilter,
    myPortfolios,
  } = usePortfolioScope();
  const sellerAccess = usePortfolioSellerAccess();
  const sellerAccessKey = portfolioSellerAccessKey(sellerAccess);
  const [trendWindowPreset, setTrendWindowPreset] =
    useState<BillingTrendWindowPreset>(DEFAULT_BILLING_TREND_WINDOW_DAYS);
  const [customTrendWindowDays, setCustomTrendWindowDays] = useState(
    String(DEFAULT_BILLING_TREND_WINDOW_DAYS),
  );
  const trendWindowDays = useMemo(() => {
    if (trendWindowPreset === "custom") {
      return clampBillingTrendWindowDays(Number(customTrendWindowDays));
    }
    return trendWindowPreset;
  }, [trendWindowPreset, customTrendWindowDays]);
  const {
    state: listState,
    setSearch,
    setFilter,
    setTrend,
    setSellerId,
    toggleSort,
    setPage,
    setPanel,
    resetFilters,
    listSearch,
  } = useCustomersListState({
    basePath,
    scopeLoading,
    sellerAccess,
    sellerAccessKey,
    sellerId: canFilterPortfolios ? sellerIdFilter : null,
    setSellerId: setSellerIdFilter,
  });

  const sellerNameByKey = useMemo(() => {
    if (canUseTeamScope) {
      return buildSellerNameByCustomerKey(sellers);
    }
    if (myPortfolios.length > 0) {
      return buildSellerNameByCustomerKey(myPortfolios);
    }
    return new Map<string, string>();
  }, [canUseTeamScope, sellers, myPortfolios]);

  const scopePortfolioIds = useMemo(
    () => filterablePortfolios.map((portfolio) => portfolio.id).filter(Boolean),
    [filterablePortfolios],
  );

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
  } = useCustomersData(canFilterPortfolios ? sellerIdFilter : null, {
    sellerNameByKey,
    listState,
    trendWindowDays,
  });

  const portfolioShare = usePortfolioBillingShare({
    sellerId: canFilterPortfolios ? sellerIdFilter : null,
  });

  const [productQuery, setProductQuery] = useState("");
  const productMatchedCustomers = useMemo(() => {
    const q = productQuery.trim().toLocaleLowerCase("pt-BR");
    if (!q) return filteredCustomers;
    return filteredCustomers.filter((customer) =>
      customer.lines.some((line) =>
        (line.produto || "").toLocaleLowerCase("pt-BR").includes(q),
      ),
    );
  }, [filteredCustomers, productQuery]);
  const productPagedCustomers = useMemo(() => {
    const size = 20;
    const start = (Math.max(1, page) - 1) * size;
    return productMatchedCustomers.slice(start, start + size);
  }, [productMatchedCustomers, page]);
  const coverageCustomers = useMemo(
    () =>
      (aggregation?.customers ?? []).map((customer) => ({
        codigo: customer.codigo,
        loja: customer.loja,
      })),
    [aggregation],
  );
  const sharedCoverage = useCustomerSharedCoverage(
    coverageCustomers,
    scopePortfolioIds,
  );
  const {
    q: search,
    focus: filter,
    trend,
    sort: sortKey,
    dir: sortDirection,
    page: requestedPage,
    panel,
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
  useEffect(() => {
    if (enrichmentIncomplete && trend !== "all") setTrend("all");
  }, [enrichmentIncomplete, setTrend, trend]);
  const hasActiveFilters =
    Boolean(search.trim()) ||
    filter !== "all" ||
    trend !== "all" ||
    listState.sellerId !== null;
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
    { id: "active", label: "Em dia" },
    { id: "no_sale_60", label: "Sem venda 60d" },
  ];
  const trendOptions: Array<{ id: CustomerTrendFilter; label: string }> = [
    { id: "all", label: "Todas" },
    { id: "up", label: "Crescimento" },
    { id: "stable", label: "Estável" },
    { id: "down", label: "Queda" },
  ];
  const scopedCustomers = aggregation?.customers ?? [];
  const overdueCustomerCount = useMemo(
    () => scopedCustomers.filter((customer) => customer.quantidadePedidosAtrasados > 0).length,
    [scopedCustomers],
  );
  const focusChips = focusOptions.map((option) => {
    const count = scopedCustomers.filter(
      (customer) =>
        matchesOperationalFocus(customer, option.id) &&
        matchesBillingTrend(customer, trend),
    ).length;
    const unavailable = option.id === "no_sale_60" && enrichmentIncomplete;
    return {
      id: option.id,
      label: `${option.label} (${count.toLocaleString("pt-BR")})${unavailable ? " · indisponível" : ""}`,
      active: filter === option.id,
      onSelect: unavailable ? undefined : () => setFilter(option.id),
    };
  });
  const trendChips = trendOptions.map((option) => {
    const count = scopedCustomers.filter(
      (customer) =>
        matchesOperationalFocus(customer, filter) &&
        matchesBillingTrend(customer, option.id),
    ).length;
    const unavailable = option.id !== "all" && enrichmentIncomplete;
    return {
      id: option.id,
      label: `${option.label} (${count.toLocaleString("pt-BR")})${unavailable ? " · indisponível" : ""}`,
      active: trend === option.id,
      onSelect: unavailable ? undefined : () => setTrend(option.id),
    };
  });
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
      id: "overdue-customers",
      label: "Com atraso",
      value: overdueCustomerCount.toLocaleString("pt-BR"),
    },
    {
      id: "filtered",
      label: "Após filtros",
      value: filteredCustomers.length.toLocaleString("pt-BR"),
    },
    ...(portfolioShare.allowed
      ? [
          {
            id: "share",
            label: "Share empresa",
            value: portfolioShare.shareLabel,
            tone: "neutral" as const,
          },
        ]
      : []),
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
            {overdueCustomerCount > 0 ? (
              <CommercialActionButton
                variant="default"
                title={CM_HELP.customers.lateOrdersShortcut}
                onClick={() =>
                  navigatePluginView("open_orders", {
                    basePath,
                    search: "?focus=late",
                  })
                }
              >
                <TriangleAlert size={16} aria-hidden="true" />
                Ver atrasos ({overdueCustomerCount.toLocaleString("pt-BR")})
              </CommercialActionButton>
            ) : null}
            <CommercialActionButton
              variant="ghost"
              onClick={reload}
              disabled={loading || refreshing}
              aria-busy={refreshing || loading}
            >
              <RefreshCw
                size={16}
                aria-hidden="true"
                className={refreshing ? "cm-spin" : undefined}
              />
              {refreshing || loading ? "Atualizando…" : "Atualizar"}
            </CommercialActionButton>
          </div>
        }
      >
        <div className="cm-customers-page__chip-row">
          <CommercialScopeChipBar
            label={
              <CommercialSectionHintLabel
                label="Foco"
                hint={CM_HELP.customers.filterFocus}
              />
            }
            aria-label="Foco operacional da carteira"
            chips={focusChips}
          />
          <CommercialScopeChipBar
            label={
              <CommercialSectionHintLabel
                label="Tendência"
                hint={CM_HELP.customers.filterTrend}
              />
            }
            aria-label="Tendência de faturamento da carteira"
            chips={trendChips}
          />
        </div>
        <CommercialFilterBarShell
          embedded
          ariaLabel="Janela da tendência, busca e escopo da carteira"
          className="cm-customers-page__filter-bar"
        >
          <div className="cm-customers-page__trend-window">
            <CommercialSectionHintLabel
              label="Janela da tendência"
              hint={CM_HELP.customers.trendWindow}
            />
            <div className="cm-customers-page__trend-window-controls">
              <CommercialSegmentToggle
                ariaLabel={CM_HELP.customers.trendWindow}
                idPrefix="customers-trend-window"
                value={String(trendWindowPreset)}
                onChange={(value) => {
                  if (value === "custom") {
                    setTrendWindowPreset("custom");
                    return;
                  }
                  const days = Number(value);
                  if ((BILLING_TREND_WINDOW_PRESETS as readonly number[]).includes(days)) {
                    setTrendWindowPreset(days as (typeof BILLING_TREND_WINDOW_PRESETS)[number]);
                  }
                }}
                options={[
                  ...BILLING_TREND_WINDOW_PRESETS.map((days) => ({
                    value: String(days),
                    label: `${days}d`,
                  })),
                  { value: "custom", label: "Personalizado" },
                ]}
              />
              {trendWindowPreset === "custom" ? (
                <CommercialTextField
                  className="cm-customers-page__trend-window-days"
                  label="Dias"
                  hint={CM_HELP.customers.trendWindowCustom}
                  type="number"
                  value={customTrendWindowDays}
                  onChange={setCustomTrendWindowDays}
                  placeholder="1–365"
                />
              ) : null}
            </div>
          </div>
          <CommercialTextField
            className="cm-customers-page__search-field"
            label="Buscar cliente"
            hint={CM_HELP.customers.filterSearch}
            type="search"
            value={search}
            onChange={setSearch}
            placeholder="Código ou nome"
          />
          <CommercialTextField
            className="cm-customers-page__search-field"
            label="Produto (pedido aberto)"
            hint="Clientes com linha em aberto cujo código contém o texto. Família/grupo (B1_GRUPO) na lista = ADR-003 até open-orders expor product_group."
            type="search"
            value={productQuery}
            onChange={setProductQuery}
            placeholder="Código do produto"
          />
          {canFilterPortfolios ? (
            <SellerScopeFilter
              sellers={filterablePortfolios}
              value={sellerIdFilter}
              onChange={setSellerId}
              hint={CM_HELP.customers.sellerScope}
              teamScope={canUseTeamScope}
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
        <CommercialEmptyState title="Carteira vazia" message={portfolioMessage} />
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

      {aggregation && hasData && !showInitialLoading && !portfolioEmpty ? (
        <>
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
            <CommercialEmptyState
              title="Nenhum cliente em aberto"
              message="Não há pedidos de venda em aberto para os clientes da carteira no momento."
            />
          ) : null}

          {showFilteredEmpty ? (
            <CommercialEmptyState
              title="Nenhum resultado"
              message="Nenhum cliente corresponde à busca e aos filtros."
            >
                <CommercialActionButton variant="ghost" onClick={resetFilters}>
                  Limpar busca e filtros
                </CommercialActionButton>
            </CommercialEmptyState>
          ) : null}

          {!showEmptyDataset ? (
            <div className="cm-customers-page__panels">
              <CommercialSegmentToggle
                ariaLabel="Painel da carteira"
                idPrefix="customers-workspace-panel"
                value={panel}
                onChange={(value) => {
                  if (value === "billing" || value === "ranking" || value === "customers") {
                    setPanel(value);
                  }
                }}
                options={[
                  { value: "billing", label: "Faturamento" },
                  { value: "ranking", label: "Ranking" },
                  { value: "customers", label: "Clientes" },
                ]}
              />

              <div
                className="cm-customers-page__panel"
                hidden={panel !== "billing"}
                aria-hidden={panel !== "billing"}
              >
                <CustomerBillingSeriesChart
                  customers={aggregation.customers}
                  active={panel === "billing"}
                />
              </div>

              <div
                className="cm-customers-page__panel"
                hidden={panel !== "ranking"}
                aria-hidden={panel !== "ranking"}
              >
                <PortfolioBillingRankingTable
                  sellerId={canFilterPortfolios ? sellerIdFilter : null}
                  active={panel === "ranking"}
                />
              </div>

              <div
                className="cm-customers-page__panel"
                hidden={panel !== "customers"}
                aria-hidden={panel !== "customers"}
              >
                {!showFilteredEmpty ? (
                  <CommercialSectionCard
                    title="Clientes da carteira"
                    hint={CM_HELP.customers.list}
                  >
                    <CustomersTable
                      customers={productPagedCustomers}
                      exportRows={productMatchedCustomers}
                      canUseTeamScope={canUseTeamScope}
                      sortKey={sortKey}
                      sortDirection={sortDirection}
                      onSort={toggleSort}
                      basePath={basePath}
                      listSearch={listSearch}
                      sellerAccess={sellerAccess}
                      loading={refreshing}
                      sharedCoverageByKey={sharedCoverage.byKey}
                    />
                    {productMatchedCustomers.length > 20 ? (
                      <CommercialPagination
                        page={page}
                        pageSize={20}
                        total={productMatchedCustomers.length}
                        onPageChange={setPage}
                      />
                    ) : null}
                  </CommercialSectionCard>
                ) : null}
              </div>
            </div>
          ) : null}
        </>
      ) : null}

      <MyPortfolioAuditSection
        sellerIdFilter={canFilterPortfolios ? sellerIdFilter : null}
        myPortfolios={myPortfolios}
        filterablePortfolios={filterablePortfolios}
      />
    </section>
  );
}
