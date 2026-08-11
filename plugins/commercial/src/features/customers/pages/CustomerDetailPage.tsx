import { useCallback, useEffect, useMemo, useState } from "react";

import { navigatePluginPath, navigatePluginView } from "../../../app/pluginNavigation";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialStateBanner,
} from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAttentionOrders } from "../components/CustomerAttentionOrders";
import { CustomerBillingPanel } from "../billing/components/CustomerBillingPanel";
import { CustomerDetailSections } from "../components/CustomerDetailSections";
import { CustomerDetailHeader } from "../components/CustomerDetailHeader";
import { CustomerActivityTimelinePanel } from "../components/CustomerActivityTimelinePanel";
import { CustomerOrdersTable } from "../components/CustomerOrdersTable";
import { CustomerOverviewSection } from "../components/CustomerOverviewSection";
import { CustomerSectionComingSoon } from "../components/CustomerSectionComingSoon";
import { useCustomerBilling } from "../billing/hooks/useCustomerBilling";
import { useCustomerDetailData } from "../hooks/useCustomerDetailData";
import { useCustomerActivities } from "../hooks/useCustomerActivities";
import { hasCustomerEnrichmentCoverage } from "../utils/customerEnrichmentCoverage";
import {
  buildCustomerDetailSearch,
  customerDetailPanelId,
  customerDetailTabId,
  parseCustomerDetailSection,
  resolveCustomerDetailFetchPolicy,
  type CustomerDetailSection,
} from "../utils/customerDetailSection";
import { buildSellerNameByCustomerKey } from "../utils/sellerNameByCustomer";
import {
  buildCustomersListPath,
  parseCustomersListDeepLink,
  type CustomersListSellerAccess,
} from "../../../utils/customersListDeepLink";

type CustomerDetailPageProps = {
  codigo: string;
  loja: string;
  basePath: string;
  search?: string;
};

/**
 * Detalhe do cliente: visão geral, pedidos, histórico NF e abas stub.
 */
export function CustomerDetailPage({
  codigo,
  loja,
  basePath,
  search,
}: CustomerDetailPageProps) {
  const {
    canUseTeamScope,
    sellers,
    myPortfolio,
    canViewWorklist,
    canManageFollowups,
    canViewAnalytics,
    canViewProposals,
  } = usePortfolioScope();

  const sellerAccess = useMemo<CustomersListSellerAccess>(
    () => ({
      allowSellerId: canUseTeamScope,
      validSellerIds: canUseTeamScope ? sellers.map((seller) => seller.id) : [],
    }),
    [canUseTeamScope, sellers],
  );
  const listDeepLink = parseCustomersListDeepLink(
    search ?? (typeof window !== "undefined" ? window.location.search : ""),
    sellerAccess,
  );

  const sellerNameByKey = useMemo(() => {
    if (canUseTeamScope) return buildSellerNameByCustomerKey(sellers);
    if (myPortfolio) return buildSellerNameByCustomerKey([myPortfolio]);
    return new Map<string, string>();
  }, [canUseTeamScope, sellers, myPortfolio]);

  const {
    loading,
    refreshing,
    error,
    hasData,
    lastSuccessAt,
    reload,
    customer: rawCustomer,
    orders,
    attentionOrders,
    listData,
  } = useCustomerDetailData(codigo, loja, {
    sellerNameByKey,
    sellerId: listDeepLink.sellerId,
  });

  const customer = rawCustomer;

  const [section, setSection] = useState<CustomerDetailSection>(() =>
    parseCustomerDetailSection(
      search ?? (typeof window !== "undefined" ? window.location.search : ""),
    ),
  );

  useEffect(() => {
    const sync = () => {
      setSection(parseCustomerDetailSection(window.location.search));
    };
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const changeSection = useCallback(
    (next: CustomerDetailSection) => {
      setSection(next);
      const path = `${basePath}/customers/${encodeURIComponent(codigo)}/${encodeURIComponent(loja)}`;
      const query = buildCustomerDetailSearch(
        next,
        typeof window !== "undefined" ? window.location.search : search,
      );
      navigatePluginPath(`${path}${query}`);
    },
    [basePath, codigo, loja, search],
  );

  const fetchPolicy = resolveCustomerDetailFetchPolicy({
    section,
    hasCustomer: Boolean(customer),
    canViewWorklist,
  });
  const billing = useCustomerBilling(codigo, loja, fetchPolicy.billing);
  const activities = useCustomerActivities(
    codigo,
    loja,
    fetchPolicy.activities,
  );

  const goBack = () => {
    const currentSearch =
      typeof window !== "undefined" ? window.location.search : search;
    const deepLink = parseCustomersListDeepLink(currentSearch, sellerAccess);
    navigatePluginPath(buildCustomersListPath(basePath, deepLink, sellerAccess));
  };
  const codeStore = formatEntityCodeStore(codigo, loja) ?? `${codigo}-${loja}`;
  const showInitialLoading = loading && !hasData;
  const notFound = hasData && !loading && customer === null;
  const canScheduleFollowUp = canViewWorklist && canManageFollowups;
  const scheduleFollowUp = canScheduleFollowUp
    ? () => {
        const params = new URLSearchParams({
          createTask: "1",
          customer_code: codigo,
          customer_store: loja,
        });
        navigatePluginView("my_day", {
          basePath,
          search: `?${params.toString()}`,
        });
      }
    : undefined;
  const refreshActiveSection = () => {
    reload();
    if (section === "historico") billing.reload();
    if (section === "atividades") activities.reload();
  };

  return (
    <div className="cm-customer-detail-page">
      <CustomerDetailHeader
        customer={customer}
        codigo={codigo}
        loja={loja}
        lastSuccessAt={lastSuccessAt}
        refreshing={refreshing}
        loading={loading}
        notFound={notFound}
        onBack={goBack}
        backHref={buildCustomersListPath(basePath, listDeepLink, sellerAccess)}
        onReload={refreshActiveSection}
        onScheduleFollowUp={scheduleFollowUp}
        canViewProposals={canViewProposals}
        basePath={basePath}
      />

      {showInitialLoading ? (
        <CommercialLoadingCard title="Carregando dados do cliente…" variant="panel" />
      ) : null}

      {error && !hasData ? (
        <CommercialStateBanner variant="error">
          <p>{error}</p>
          <div className="cm-customer-detail__actions">
            <CommercialActionButton variant="ghost" onClick={reload}>
              Tentar novamente
            </CommercialActionButton>
            <CommercialActionButton variant="ghost" onClick={goBack}>
              Voltar para clientes
            </CommercialActionButton>
          </div>
        </CommercialStateBanner>
      ) : null}

      {error && hasData ? (
        <CommercialStateBanner>
          <p>Não foi possível atualizar os pedidos em aberto: {error}</p>
          <CommercialActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing}
          >
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {customer && listData.enrichment.error ? (
        <CommercialStateBanner>
          <p>
            Cadastro e faturamento com cobertura parcial
            {listData.enrichment.total > 0
              ? ` (${listData.enrichment.covered}/${listData.enrichment.total})`
              : ""}
            : {listData.enrichment.error}
          </p>
          <CommercialActionButton
            variant="ghost"
            onClick={reload}
            disabled={refreshing || listData.enrichment.loading}
          >
            Tentar novamente
          </CommercialActionButton>
        </CommercialStateBanner>
      ) : null}

      {notFound ? (
        <CommercialEmptyState
          title="Cliente não encontrado"
          message={`Não há pedidos de venda em aberto para o código / loja ${codeStore} no momento.`}
        >
            <CommercialActionButton variant="ghost" onClick={goBack}>
              Voltar para clientes
            </CommercialActionButton>
        </CommercialEmptyState>
      ) : null}

      {customer ? (
        <>
          <CustomerDetailSections
            section={section}
            onChange={changeSection}
            openOrdersCount={customer.quantidadePedidosAbertos}
          />

          <main
              className="cm-customer-overview__main"
              id={customerDetailPanelId(section)}
              role="tabpanel"
              aria-labelledby={customerDetailTabId(section)}
              tabIndex={0}
            >
              {section === "resumo" ? (
                <CustomerOverviewSection
                  customer={customer}
                  orders={orders}
                  loading={refreshing}
                  activities={activities}
                  canViewActivities={canViewWorklist}
                  canViewAnalytics={canViewAnalytics}
                  coveragePartial={
                    !listData.enrichment.loading &&
                    !hasCustomerEnrichmentCoverage(customer)
                  }
                  basePath={basePath}
                  onGoToOrders={() => changeSection("pedidos")}
                  onGoToActivities={() => changeSection("atividades")}
                />
              ) : null}

              {section === "pedidos" ? (
                <>
                  <CustomerAttentionOrders orders={attentionOrders} />
                  {orders.length === 0 ? (
                    <CommercialStateBanner>
                      Cliente localizado, porém sem linhas utilizáveis neste recorte.
                    </CommercialStateBanner>
                  ) : (
                    <CustomerOrdersTable
                      orders={orders}
                      basePath={basePath}
                      canViewAnalytics={canViewAnalytics}
                    />
                  )}
                </>
              ) : null}

              {section === "historico" ? <CustomerBillingPanel billing={billing} /> : null}

              {section === "oportunidades" ? (
                <CustomerSectionComingSoon
                  basePath={basePath}
                  customerCode={codigo}
                  canViewAnalytics={canViewAnalytics}
                />
              ) : null}

              {section === "atividades" ? (
                <CustomerActivityTimelinePanel
                  activities={activities}
                  canViewActivities={canViewWorklist}
                  onScheduleFollowUp={scheduleFollowUp}
                />
              ) : null}
            </main>
        </>
      ) : null}
    </div>
  );
}
