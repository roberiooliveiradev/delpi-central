import { ActionButton, EmptyState } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useReducer, useState, type MouseEvent } from "react";

import { getOpsAbertas, getOpenOrdersTotvs } from "../../api/openOrdersTotvsApi";
import {
  cmEmptyStateClassNames,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import { resolvePagePathBack } from "../../app/commercialNavigationReturn";
import { navigatePluginPath } from "../../app/pluginNavigation";
import {
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildPluginPath,
} from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { usePortfolioSellerAccess } from "../../app/usePortfolioSellerAccess";
import { OpenOrdersProductionDetailContent } from "../../components/OpenOrdersProductionDetailContent";
import { InteractionRoomPanel } from "../interaction-rooms/InteractionRoomPanel";
import {
  buildProductionOrderEntityKey,
  INTERACTION_ENTITY_TYPES,
} from "../interaction-rooms/interactionRoomEntityKeys";
import { resolveOpenOrderOpDetailItem } from "../../utils/enrichOpenOrdersForecast";
import {
  buildOpenOrdersContextSearch,
  resolveOpenOrdersSellerId,
} from "../../utils/openOrdersDeepLink";
import {
  buildOpenOrderOpRouteIdentity,
  INITIAL_OPEN_ORDER_OP_DETAIL_STATE,
  reduceOpenOrderOpDetailState,
  selectOpenOrderOpSnapshot,
} from "./openOrderOpDetailState";

type OpenOrderOpDetailPageProps = {
  basePath: string;
  branch: string;
  orderNumber: string;
  lineItem: string;
  productionOrder: string;
  search?: string;
};

export function OpenOrderOpDetailPage({
  basePath,
  branch,
  orderNumber,
  lineItem,
  productionOrder,
  search,
}: OpenOrderOpDetailPageProps) {
  const [loadState, dispatchLoad] = useReducer(
    reduceOpenOrderOpDetailState,
    INITIAL_OPEN_ORDER_OP_DETAIL_STATE,
  );
  const [reloadKey, setReloadKey] = useState(0);
  const { loading: scopeLoading } = usePortfolioScope();
  const sellerAccess = usePortfolioSellerAccess();
  const sourceSearch = search ?? (typeof window !== "undefined" ? window.location.search : "");
  const sellerId = useMemo(
    () => resolveOpenOrdersSellerId(new URLSearchParams(sourceSearch).get("seller_id"), sellerAccess),
    [sellerAccess, sourceSearch],
  );
  const routeIdentity = buildOpenOrderOpRouteIdentity({
    branch,
    orderNumber,
    lineItem,
    productionOrder,
  });
  const item = selectOpenOrderOpSnapshot(loadState, routeIdentity);
  const requestBelongsToRoute = loadState.requestIdentity === routeIdentity;
  const loading = scopeLoading ||
    loadState.status === "loading" || (!requestBelongsToRoute && item === null);
  const refreshing = requestBelongsToRoute && loadState.status === "refreshing";
  const contextSearch = useMemo(
    () => buildOpenOrdersContextSearch(sourceSearch, sellerAccess),
    [sellerAccess, sourceSearch],
  );
  const ordersHref = buildPluginPath("open_orders", basePath, contextSearch);
  const lineHref = buildOpenOrderLineDetailPath(
    basePath,
    branch,
    orderNumber,
    lineItem,
    contextSearch,
  ) ?? ordersHref;
  const back = resolvePagePathBack(
    sourceSearch,
    { href: lineHref, label: "Detalhe da linha" },
    basePath,
  );

  useEffect(() => {
    if (scopeLoading) return;
    const controller = new AbortController();
    dispatchLoad({ type: "request_started", identity: routeIdentity });

    void (async () => {
      try {
        const pedidosPromise = getOpenOrdersTotvs(controller.signal, { sellerId });
        const opsPromise = getOpsAbertas(controller.signal).catch(() => null);
        const [data, opsData] = await Promise.all([pedidosPromise, opsPromise]);
        if (controller.signal.aborted) return;
        const matched = resolveOpenOrderOpDetailItem(data.items, opsData, {
          filial: branch,
          pedido: orderNumber,
          linha: lineItem,
          productionOrder,
        });
        if (!matched) {
          dispatchLoad({
            type: "request_not_found",
            identity: routeIdentity,
            message: data.portfolio?.empty
              ? data.portfolio.message || "Nenhum pedido disponível neste escopo."
              : "A linha ou a OP não foi encontrada no escopo atual.",
          });
          return;
        }
        dispatchLoad({ type: "request_succeeded", identity: routeIdentity, item: matched });
      } catch (reason: unknown) {
        if (controller.signal.aborted) return;
        dispatchLoad({
          type: "request_failed",
          identity: routeIdentity,
          message: reason instanceof Error
            ? reason.message
            : "Não foi possível carregar o detalhe da OP.",
        });
      }
    })();

    return () => controller.abort();
  }, [
    branch,
    lineItem,
    orderNumber,
    productionOrder,
    reloadKey,
    routeIdentity,
    scopeLoading,
    sellerId,
  ]);

  const navigateBack = (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    navigatePluginPath(back.href);
  };

  const selectProductionOrder = (nextProductionOrder: string) => {
    const target = buildOpenOrderOpDetailPath(
      basePath,
      branch,
      orderNumber,
      lineItem,
      nextProductionOrder,
      contextSearch,
    );
    if (target) navigatePluginPath(target);
  };

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{ label: back.label, href: back.href, onNavigate: navigateBack }}
        items={[
          {
            id: "orders",
            label: "Pedidos em aberto",
            href: ordersHref,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginPath(ordersHref);
            },
          },
          {
            id: "line",
            label: `Pedido ${orderNumber} · linha ${lineItem}`,
            href: lineHref,
            onNavigate: navigateBack,
          },
        ]}
        current={`${item?.produto?.trim() ? `Produto ${item.produto.trim()} · ` : ""}OP ${productionOrder}`}
      />

      <CommercialPageHero
        eyebrow="Produção do pedido"
        title={`OP ${productionOrder}`}
        description={`Pedido ${orderNumber} · linha ${lineItem} · filial ${branch}`}
        actions={
          <ActionButton
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
            disabled={refreshing}
            aria-busy={refreshing}
          >
            <RefreshCw size={16} aria-hidden="true" className={refreshing ? "cm-spin" : undefined} />
            {refreshing ? "Atualizando…" : "Atualizar"}
          </ActionButton>
        }
      />

      {loading ? <CommercialLoadingCard title="Carregando detalhe da OP…" variant="panel" /> : null}
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
        <>
          <OpenOrdersProductionDetailContent
            item={item}
            basePath={basePath}
            productionOrder={productionOrder}
            search={contextSearch}
            onProductionOrderChange={selectProductionOrder}
            showOpenProductionOrderAction={false}
          />
          <InteractionRoomPanel
            basePath={basePath}
            entityType={INTERACTION_ENTITY_TYPES.productionOrder}
            entityKey={buildProductionOrderEntityKey(branch, productionOrder)}
            roomTitle={`OP ${productionOrder}`}
          />
        </>
      ) : null}
    </section>
  );
}
