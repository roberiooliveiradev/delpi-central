import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { navigatePluginPath, navigatePluginView } from "../../../app/pluginNavigation";
import { CommercialPagePath } from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { EmptyState } from "../../../ui/EmptyState";
import { PVA_STATE_BOX } from "../../../ui/stateChrome";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAttentionOrders } from "../components/CustomerAttentionOrders";
import { CustomerBillingPanel } from "../billing/components/CustomerBillingPanel";
import { CustomerDetailSections } from "../components/CustomerDetailSections";
import { CustomerDetailHeader } from "../components/CustomerDetailHeader";
import { CustomerAccountRail } from "../components/CustomerAccountRail";
import { CustomerActivityTimelinePanel } from "../components/CustomerActivityTimelinePanel";
import { CustomerOrdersTable } from "../components/CustomerOrdersTable";
import { CustomerOverviewSection } from "../components/CustomerOverviewSection";
import { CustomerSectionComingSoon } from "../components/CustomerSectionComingSoon";
import { useCustomerBilling } from "../billing/hooks/useCustomerBilling";
import { useCustomerDetailData } from "../hooks/useCustomerDetailData";
import { useCustomerActivities } from "../hooks/useCustomerActivities";
import {
  buildCustomerDetailSearch,
  customerDetailPanelId,
  customerDetailTabId,
  isHistorySection,
  parseCustomerDetailSection,
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

  const billing = useCustomerBilling(
    codigo,
    loja,
    Boolean(customer) && isHistorySection(section),
  );
  const activities = useCustomerActivities(
    codigo,
    loja,
    Boolean(customer) && section === "atividades" && canViewWorklist,
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
    <div className="pva-internal-page pva-checkup-page">
      {!customer ? (
        <header className="pva-detail-header pva-detail-header--minimal">
          <CommercialPagePath
            back={{
              label: "Minha carteira",
              href: buildCustomersListPath(basePath, listDeepLink, sellerAccess),
              onNavigate: (event) => {
                event.preventDefault();
                goBack();
              },
            }}
            current={notFound ? "Cliente não encontrado" : `Carregando ${codeStore}…`}
          />
          <div className="pva-detail-header__row">
            <div>
              <h1 className="pva-detail-header__name">Cliente</h1>
              <p className="pva-checkup__code">Código / loja: {codeStore}</p>
            </div>
            {!notFound ? (
              <button
                type="button"
                className="pva-btn pva-btn--ghost"
                onClick={refreshActiveSection}
                disabled={loading || refreshing}
                aria-busy={refreshing || loading}
              >
                <RefreshCw
                  size={16}
                  aria-hidden="true"
                  className={refreshing ? "pva-spin" : undefined}
                />
                {refreshing || loading ? "Atualizando…" : "Atualizar seção"}
              </button>
            ) : null}
          </div>
        </header>
      ) : (
        <CustomerDetailHeader
          customer={customer}
          lastSuccessAt={lastSuccessAt}
          refreshing={refreshing}
          loading={loading}
          onBack={goBack}
          backHref={buildCustomersListPath(basePath, listDeepLink, sellerAccess)}
          onReload={refreshActiveSection}
          onScheduleFollowUp={scheduleFollowUp}
        />
      )}

      {showInitialLoading ? (
        <div className={PVA_STATE_BOX} role="status">
          Carregando dados do cliente…
        </div>
      ) : null}

      {error && !hasData ? (
        <div className="pva-alert pva-alert--error" role="alert">
          <p>{error}</p>
          <div className="pva-checkup__actions">
            <button type="button" className="pva-btn pva-btn--secondary" onClick={reload}>
              Tentar novamente
            </button>
            <button type="button" className="pva-btn pva-btn--secondary" onClick={goBack}>
              Voltar para clientes
            </button>
          </div>
        </div>
      ) : null}

      {error && hasData ? (
        <div className="pva-alert pva-alert--warning" role="alert">
          <p>Não foi possível atualizar os pedidos em aberto: {error}</p>
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

      {customer && listData.enrichment.error ? (
        <div className="pva-alert pva-alert--warning" role="status">
          <p>
            Cadastro e faturamento com cobertura parcial
            {listData.enrichment.total > 0
              ? ` (${listData.enrichment.covered}/${listData.enrichment.total})`
              : ""}
            : {listData.enrichment.error}
          </p>
          <button
            type="button"
            className="pva-btn pva-btn--secondary"
            onClick={reload}
            disabled={refreshing || listData.enrichment.loading}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {notFound ? (
        <EmptyState
          title="Cliente não encontrado"
          description={`Não há pedidos de venda em aberto para o código / loja ${codeStore} no momento.`}
          action={
            <button type="button" className="pva-btn pva-btn--secondary" onClick={goBack}>
              Voltar para clientes
            </button>
          }
        />
      ) : null}

      {customer ? (
        <>
          <CustomerDetailSections
            section={section}
            onChange={changeSection}
            openOrdersCount={customer.quantidadePedidosAbertos}
          />

          <div className="pva-customer-overview__grid">
            <div className="pva-customer-account-rail-slot--mobile">
              <CustomerAccountRail
                customer={customer}
                basePath={basePath}
                canViewProposals={canViewProposals}
                onViewOrders={() => changeSection("pedidos")}
              />
            </div>
            <main
              className="pva-customer-overview__main"
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
                  onGoToOrders={() => changeSection("pedidos")}
                  onGoToActivities={() => changeSection("atividades")}
                />
              ) : null}

              {section === "pedidos" ? (
                <>
                  <CustomerAttentionOrders orders={attentionOrders} />
                  {orders.length === 0 ? (
                    <div className={PVA_STATE_BOX} role="status">
                      Cliente localizado, porém sem linhas utilizáveis neste recorte.
                    </div>
                  ) : (
                    <CustomerOrdersTable orders={orders} basePath={basePath} />
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
            <aside className="pva-customer-overview__side pva-customer-account-rail-slot--desktop">
              <CustomerAccountRail
                customer={customer}
                basePath={basePath}
                canViewProposals={canViewProposals}
                onViewOrders={() => changeSection("pedidos")}
              />
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}
