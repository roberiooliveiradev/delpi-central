import { useCallback, useEffect, useMemo, useState } from "react";

import { navigatePluginPath, navigatePluginView } from "../../../app/pluginNavigation";
import {
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialStateBanner,
} from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { usePortfolioSellerAccess } from "../../../app/usePortfolioSellerAccess";
import { CM_HELP } from "../../../content/helpTooltips";
import { CustomerAttentionOrders } from "../components/CustomerAttentionOrders";
import { CustomerBillingPanel } from "../billing/components/CustomerBillingPanel";
import { CustomerDetailSections } from "../components/CustomerDetailSections";
import { CustomerDetailHeader } from "../components/CustomerDetailHeader";
import { AccountContactsPanel } from "../components/AccountContactsPanel";
import { CustomerActivityTimelinePanel } from "../components/CustomerActivityTimelinePanel";
import { CustomerOpportunitiesSection } from "../components/CustomerOpportunitiesSection";
import { CustomerOrdersTable } from "../components/CustomerOrdersTable";
import { CustomerOverviewSection } from "../components/CustomerOverviewSection";
import { useCustomerBilling } from "../billing/hooks/useCustomerBilling";
import { useCustomerDetailData } from "../hooks/useCustomerDetailData";
import { useCustomerActivities } from "../hooks/useCustomerActivities";
import { useCustomerSharedCoverage } from "../hooks/useCustomerSharedCoverage";
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
import { customerKey } from "../../../shared/format";
import {
  buildCustomersListPath,
  parseCustomersListDeepLink,
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
    myPortfolios,
    filterablePortfolios,
    canViewWorklist,
    canManageFollowups,
    canViewAnalytics,
    canViewProposals,
  } = usePortfolioScope();

  const sellerAccess = usePortfolioSellerAccess();
  const listDeepLink = parseCustomersListDeepLink(
    search ?? (typeof window !== "undefined" ? window.location.search : ""),
    sellerAccess,
  );

  const sellerNameByKey = useMemo(() => {
    if (canUseTeamScope) return buildSellerNameByCustomerKey(sellers);
    if (myPortfolios.length > 0) return buildSellerNameByCustomerKey(myPortfolios);
    return new Map<string, string>();
  }, [canUseTeamScope, sellers, myPortfolios]);

  const scopePortfolioIds = useMemo(
    () => filterablePortfolios.map((portfolio) => portfolio.id).filter(Boolean),
    [filterablePortfolios],
  );
  const sharedCoverage = useCustomerSharedCoverage(
    [{ codigo: codigo, loja: loja }],
    scopePortfolioIds,
  );
  const customerSharedCoverage =
    sharedCoverage.byKey.get(customerKey(codigo, loja)) ?? null;

  const {
    loading,
    refreshing,
    error,
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
  const [contactsRefreshKey, setContactsRefreshKey] = useState(0);

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
  const showInitialLoading = loading && !customer;
  const canScheduleFollowUp = canViewWorklist && canManageFollowups;
  const scheduleFollowUp = canScheduleFollowUp
    ? () => {
        const params = new URLSearchParams({
          createTask: "1",
          customer_code: codigo,
          customer_store: loja,
        });
        navigatePluginView("my_tasks", {
          basePath,
          search: `?${params.toString()}`,
        });
      }
    : undefined;
  const refreshActiveSection = () => {
    reload();
    if (section === "historico") billing.reload();
    if (section === "atividades") activities.reload();
    if (section === "contatos") setContactsRefreshKey((current) => current + 1);
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
        onBack={goBack}
        backHref={buildCustomersListPath(basePath, listDeepLink, sellerAccess)}
        onReload={refreshActiveSection}
        onScheduleFollowUp={scheduleFollowUp}
        canViewProposals={canViewProposals}
        basePath={basePath}
        sharedCoverage={customerSharedCoverage}
      />

      {showInitialLoading ? (
        <CommercialLoadingCard title="Carregando dados do cliente…" variant="panel" />
      ) : null}

      {error && !customer ? (
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

      {error && customer ? (
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
                      {CM_HELP.customerDetail.ordersScopeEmpty}
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
                <CustomerOpportunitiesSection
                  basePath={basePath}
                  customerCode={codigo}
                  canViewAnalytics={canViewAnalytics}
                />
              ) : null}

              {section === "contatos" ? (
                <AccountContactsPanel
                  customerCode={codigo}
                  customerStore={loja}
                  refreshKey={contactsRefreshKey}
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
