import { ActionButton, EmptyState } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useReducer, useState, type MouseEvent } from "react";

import { getOpenOrdersTotvs } from "../../api/openOrdersTotvsApi";
import {
  cmEmptyStateClassNames,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { usePortfolioSellerAccess } from "../../app/usePortfolioSellerAccess";
import { OpenOrdersProductionDetailContent } from "../../components/OpenOrdersProductionDetailContent";
import {
  buildOpenOrdersContextSearch,
  findOpenOrderLine,
  resolveOpenOrdersSellerId,
} from "../../utils/openOrdersDeepLink";
import {
  buildOpenOrderLineRouteIdentity,
  INITIAL_OPEN_ORDER_LINE_DETAIL_STATE,
  reduceOpenOrderLineDetailState,
  selectOpenOrderLineSnapshot,
} from "./openOrderLineDetailState";

type OpenOrderLineDetailPageProps = {
  basePath: string;
  branch: string;
  orderNumber: string;
  lineItem: string;
  search?: string;
};

export function OpenOrderLineDetailPage({
  basePath,
  branch,
  orderNumber,
  lineItem,
  search,
}: OpenOrderLineDetailPageProps) {
  const [loadState, dispatchLoad] = useReducer(
    reduceOpenOrderLineDetailState,
    INITIAL_OPEN_ORDER_LINE_DETAIL_STATE,
  );
  const [reloadKey, setReloadKey] = useState(0);
  const { loading: scopeLoading } = usePortfolioScope();
  const sellerAccess = usePortfolioSellerAccess();
  const sourceSearch = search ?? (typeof window !== "undefined" ? window.location.search : "");
  const sellerId = useMemo(
    () => resolveOpenOrdersSellerId(new URLSearchParams(sourceSearch).get("seller_id"), sellerAccess),
    [sellerAccess, sourceSearch],
  );
  const routeIdentity = buildOpenOrderLineRouteIdentity({ branch, orderNumber, lineItem });
  const item = selectOpenOrderLineSnapshot(loadState, routeIdentity);
  const requestBelongsToRoute = loadState.requestIdentity === routeIdentity;
  const loading = scopeLoading ||
    loadState.status === "loading" || (!requestBelongsToRoute && item === null);
  const refreshing = requestBelongsToRoute && loadState.status === "refreshing";
  const contextSearch = useMemo(
    () => buildOpenOrdersContextSearch(sourceSearch, sellerAccess),
    [sellerAccess, sourceSearch],
  );
  const backHref = buildPluginPath("open_orders", basePath, contextSearch);

  useEffect(() => {
    if (scopeLoading) return;
    const controller = new AbortController();
    dispatchLoad({ type: "request_started", identity: routeIdentity });

    void getOpenOrdersTotvs(controller.signal, { sellerId })
      .then((data) => {
        if (controller.signal.aborted) return;
        const matched = findOpenOrderLine(data.items, {
          filial: branch,
          pedido: orderNumber,
          linha: lineItem,
        });
        if (!matched) {
          dispatchLoad({
            type: "request_not_found",
            identity: routeIdentity,
            message: data.portfolio?.empty
              ? data.portfolio.message || "Nenhum pedido disponível neste escopo."
              : "A linha não foi encontrada no escopo atual.",
          });
          return;
        }
        dispatchLoad({ type: "request_succeeded", identity: routeIdentity, item: matched });
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        dispatchLoad({
          type: "request_failed",
          identity: routeIdentity,
          message:
            reason instanceof Error
              ? reason.message
              : "Não foi possível carregar o detalhe da linha.",
        });
      });

    return () => controller.abort();
  }, [branch, lineItem, orderNumber, reloadKey, routeIdentity, scopeLoading, sellerId]);

  const navigateBack = (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    navigatePluginPath(backHref);
  };

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{ label: "Pedidos em aberto", href: backHref, onNavigate: navigateBack }}
        current={`Pedido ${orderNumber} · linha ${lineItem}`}
      />

      <CommercialPageHero
        eyebrow="Pedido em aberto"
        title={`Pedido ${orderNumber} · linha ${lineItem}`}
        description={
          item
            ? `${item.nome_cliente || "Cliente"} · Produto ${item.produto || "—"} · filial ${branch}`
            : `Filial ${branch}`
        }
        actions={
          <ActionButton
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
            disabled={refreshing}
            aria-busy={refreshing}
          >
            <RefreshCw
              size={16}
              aria-hidden="true"
              className={refreshing ? "cm-spin" : undefined}
            />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </ActionButton>
        }
      />

      {loading ? (
        <CommercialLoadingCard title="Carregando detalhe da linha…" variant="panel" />
      ) : null}
      {loadState.blockingError ? (
        <>
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage={loadState.blockingError}
            role="alert"
          />
          <ActionButton variant="primary" onClick={() => setReloadKey((value) => value + 1)}>
            Tentar novamente
          </ActionButton>
        </>
      ) : null}
      {!loading && !loadState.blockingError && loadState.blockingEmpty ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={loadState.blockingEmpty}
          role="status"
        />
      ) : null}
      {loadState.refreshNotice && item ? (
        <div className="cm-alert cm-alert--warning" role="alert">
          <p>{loadState.refreshNotice}</p>
          <ActionButton
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
            disabled={refreshing}
          >
            Tentar novamente
          </ActionButton>
        </div>
      ) : null}
      {item ? (
        <OpenOrdersProductionDetailContent
          item={item}
          basePath={basePath}
          search={contextSearch}
        />
      ) : null}
    </section>
  );
}
