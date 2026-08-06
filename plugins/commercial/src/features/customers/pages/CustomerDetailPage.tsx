import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { navigatePluginPath, navigatePluginView } from "../../../app/pluginNavigation";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { EmptyState } from "../../../ui/EmptyState";
import { PVA_STATE_BOX } from "../../../ui/stateChrome";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { CustomerAttentionOrders } from "../components/CustomerAttentionOrders";
import { CustomerBillingPanel } from "../billing/components/CustomerBillingPanel";
import { CustomerDetailSections } from "../components/CustomerDetailSections";
import { CustomerDetailHeader } from "../components/CustomerDetailHeader";
import { CustomerOrdersTable } from "../components/CustomerOrdersTable";
import { CustomerOverviewSection } from "../components/CustomerOverviewSection";
import { CustomerSectionComingSoon } from "../components/CustomerSectionComingSoon";
import { useCustomerBilling } from "../billing/hooks/useCustomerBilling";
import { useCustomerDetailData } from "../hooks/useCustomerDetailData";
import {
  buildCustomerDetailSearch,
  isHistorySection,
  parseCustomerDetailSection,
  type CustomerDetailSection,
} from "../utils/customerDetailSection";
import { buildSellerNameByCustomerKey } from "../utils/sellerNameByCustomer";

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
  const { isAdmin, sellers, myPortfolio } = usePortfolioScope();

  const sellerNameByKey = useMemo(() => {
    if (isAdmin) return buildSellerNameByCustomerKey(sellers);
    if (myPortfolio) return buildSellerNameByCustomerKey([myPortfolio]);
    return new Map<string, string>();
  }, [isAdmin, sellers, myPortfolio]);

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
  } = useCustomerDetailData(codigo, loja, { sellerNameByKey });

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
    Boolean(customer) || isHistorySection(section),
  );

  const goBack = () => navigatePluginView("customers", { basePath });
  const codeStore = formatEntityCodeStore(codigo, loja) ?? `${codigo}-${loja}`;
  const showInitialLoading = loading && !hasData;
  const notFound = hasData && !loading && customer === null;

  return (
    <div className="pva-internal-page pva-checkup-page">
      {!customer ? (
        <header className="pva-detail-header pva-detail-header--minimal">
          <nav className="pva-detail-breadcrumb" aria-label="Navegação">
            <button type="button" className="pva-detail-breadcrumb__link" onClick={goBack}>
              Minha carteira
            </button>
            <span className="pva-detail-breadcrumb__sep" aria-hidden="true">
              /
            </span>
            <span className="pva-detail-breadcrumb__current">{codeStore}</span>
          </nav>
          <div className="pva-detail-header__row">
            <div>
              <h1 className="pva-detail-header__name">Cliente</h1>
              <p className="pva-checkup__code">Código / loja: {codeStore}</p>
            </div>
            {!notFound ? (
              <button
                type="button"
                className="pva-btn pva-btn--ghost"
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
          onReload={reload}
          onRegisterContact={() => changeSection("contatos")}
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

          {section === "resumo" ? (
            <CustomerOverviewSection
              customer={customer}
              orders={orders}
              loading={refreshing}
              onGoToOrders={() => changeSection("pedidos")}
              onGoToContacts={() => changeSection("contatos")}
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
                <CustomerOrdersTable orders={orders} />
              )}
            </>
          ) : null}

          {section === "historico" ? <CustomerBillingPanel billing={billing} /> : null}

          {section === "oportunidades" || section === "contatos" ? (
            <CustomerSectionComingSoon section={section} />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
