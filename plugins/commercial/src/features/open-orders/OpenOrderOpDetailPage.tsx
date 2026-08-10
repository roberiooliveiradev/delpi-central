import { ActionButton, EmptyState } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState, type MouseEvent } from "react";

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
import type { OpenOrdersTotvsItem } from "../../types/openOrdersTotvs";
import {
  buildOpenOrderLineReturnSearch,
  buildOpenOrdersContextSearch,
} from "../../utils/openOrdersDeepLink";
import { getLineOpForecast } from "../../utils/opAllocation";

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
  const [item, setItem] = useState<OpenOrdersTotvsItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [emptyMessage, setEmptyMessage] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const sellerId = useMemo(() => readSellerId(search), [search]);
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
    setLoading(true);
    setError(null);
    setEmptyMessage(null);
    setItem(null);

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
          setEmptyMessage(
            data.portfolio?.empty
              ? data.portfolio.message || "Nenhum pedido disponível neste escopo."
              : "A linha ou a OP não foi encontrada no escopo atual.",
          );
          return;
        }
        setItem(matched);
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Não foi possível carregar o detalhe da OP.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [branch, orderNumber, lineItem, productionOrder, sellerId, reloadKey]);

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
          <ActionButton variant="ghost" onClick={() => setReloadKey((value) => value + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </ActionButton>
        }
      />

      {loading ? <CommercialLoadingCard title="Carregando detalhe da OP…" variant="panel" /> : null}
      {error ? (
        <>
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
          <ActionButton variant="primary" onClick={() => setReloadKey((value) => value + 1)}>
            Tentar novamente
          </ActionButton>
        </>
      ) : null}
      {!loading && !error && emptyMessage ? (
        <EmptyState
          classNames={cmEmptyStateClassNames}
          defaultMessage={emptyMessage}
          role="status"
        />
      ) : null}
      {!loading && !error && item ? (
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
