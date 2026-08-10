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
import { buildOpenOrderOpDetailPath, buildPluginPath } from "../../app/pluginRoutes";
import { OpenOrdersProductionDetailContent } from "../../components/OpenOrdersLineDetailModal";
import {
  buildOpenOrderLineReturnSearch,
  buildOpenOrdersContextSearch,
} from "../../utils/openOrdersDeepLink";
import { getLineOpForecast } from "../../utils/opAllocation";
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

function readSellerId(search?: string): string | null {
  const params = new URLSearchParams(
    search ?? (typeof window !== "undefined" ? window.location.search : ""),
  );
  return (params.get("seller_id") ?? "").trim() || null;
}

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
  const sellerId = useMemo(() => readSellerId(search), [search]);
  const routeIdentity = buildOpenOrderOpRouteIdentity({
    branch,
    orderNumber,
    lineItem,
    productionOrder,
  });
  const item = selectOpenOrderOpSnapshot(loadState, routeIdentity);
  const requestBelongsToRoute = loadState.requestIdentity === routeIdentity;
  const loading =
    loadState.status === "loading" || (!requestBelongsToRoute && item === null);
  const refreshing = requestBelongsToRoute && loadState.status === "refreshing";
  const contextSearch = useMemo(() => buildOpenOrdersContextSearch(search), [search]);
  const backHref = buildPluginPath(
    "open_orders",
    basePath,
    buildOpenOrderLineReturnSearch(search, {
      pedido: orderNumber,
      linha: lineItem,
      filial: branch,
    }),
  );

  useEffect(() => {
    const controller = new AbortController();
    dispatchLoad({ type: "request_started", identity: routeIdentity });

    void getOpenOrdersTotvs(controller.signal, { sellerId })
      .then((data) => {
        if (controller.signal.aborted) return;
        const matched =
          data.items.find(
            (row) =>
              row.filial.trim() === branch &&
              row.pedido.trim() === orderNumber &&
              row.linha.trim() === lineItem,
          ) ?? null;
        const opExists = matched
          ? getLineOpForecast(matched).opsUtilizadas.some(
              (op) => op.numero_op.trim() === productionOrder,
            )
          : false;
        if (!matched || !opExists) {
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
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        dispatchLoad({
          type: "request_failed",
          identity: routeIdentity,
          message: reason instanceof Error
            ? reason.message
            : "Não foi possível carregar o detalhe da OP.",
        });
      });

    return () => controller.abort();
  }, [
    branch,
    lineItem,
    orderNumber,
    productionOrder,
    reloadKey,
    routeIdentity,
    sellerId,
  ]);

  const navigateBack = (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    navigatePluginPath(backHref);
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
        back={{ label: "Pedidos em aberto", href: backHref, onNavigate: navigateBack }}
        items={[
          {
            id: "line",
            label: `Pedido ${orderNumber} · linha ${lineItem}`,
            href: backHref,
            onNavigate: navigateBack,
          },
        ]}
        current={`OP ${productionOrder}`}
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
            <RefreshCw size={16} aria-hidden="true" className={refreshing ? "pva-spin" : undefined} />
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
        <div className="pva-alert pva-alert--warning" role="alert">
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
          productionOrder={productionOrder}
          search={search}
          onProductionOrderChange={selectProductionOrder}
        />
      ) : null}
    </section>
  );
}
