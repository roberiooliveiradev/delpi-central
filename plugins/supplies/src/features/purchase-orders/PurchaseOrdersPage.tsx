import { useEffect, useMemo, useState } from "react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { listPurchaseOrders } from "./api";
import {
  mapPurchaseOrdersFetchError,
  PURCHASE_ORDERS_CONTENT as C,
} from "./content";
import { PurchaseOrdersFilters } from "./PurchaseOrdersFilters";
import {
  buildOrderKey,
  buildUrlSearch,
  createDefaultQuery,
  formatDatePtBr,
  formatMoneyBr,
  formatProductLabel,
  labelDeliveryStatus,
  parseOrderKey,
  parseQueryFromSearch,
} from "./query";
import type { PurchaseOrderListItem, PurchaseOrdersQuery } from "./types";

type PurchaseOrdersPageProps = {
  basePath: string;
};

function readBrowserSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search || "";
}

function replaceBrowserSearch(search: string) {
  if (typeof window === "undefined") return;
  const next = `${window.location.pathname}${search}`;
  const current = `${window.location.pathname}${window.location.search || ""}`;
  if (next === current) return;
  window.history.replaceState(window.history.state, "", next);
}

function statusBadgeVariant(
  status: string | null | undefined,
): "danger" | "success" | "neutral" {
  if (status === "late") return "danger";
  if (status === "on_time") return "success";
  return "neutral";
}

export function PurchaseOrdersPage({ basePath }: PurchaseOrdersPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const defaultBranch = session.preferences?.defaultBranch || units[0] || "01";

  const [query, setQuery] = useState<PurchaseOrdersQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), defaultBranch),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<PurchaseOrderListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    if (!units.includes(query.branch) && units.length > 0) {
      setQuery((current) => ({ ...current, branch: defaultBranch, page: 1 }));
    }
  }, [defaultBranch, query.branch, units]);

  useEffect(() => {
    replaceBrowserSearch(buildUrlSearch(query));
  }, [query]);

  useEffect(() => {
    if (!query.branch) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listPurchaseOrders(query, controller.signal)
      .then((payload) => {
        setItems(payload.items ?? []);
        setTotal(payload.total ?? 0);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        const message = err instanceof Error ? err.message : C.error;
        setError(mapPurchaseOrdersFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, reloadKey]);

  const selected = useMemo(() => parseOrderKey(query.order), [query.order]);
  const selectedItem = useMemo(() => {
    if (!selected) return null;
    return (
      items.find(
        (item) =>
          item.branch === selected.branch && item.order_number === selected.orderNumber,
      ) ?? null
    );
  }, [items, selected]);

  const totalPages = Math.max(1, Math.ceil(total / query.page_size) || 1);
  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = (patch: Partial<PurchaseOrdersQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  };

  const onSelectRow = (item: PurchaseOrderListItem) => {
    patchQuery({
      order: buildOrderKey(item.branch, item.order_number),
    });
  };

  return (
    <div className="sp-page-stack sp-purchase-orders">
      <SuppliesPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={C.title}
      />

      <SuppliesPageHero
        eyebrow={C.eyebrow}
        title={
          <SuppliesSectionHintLabel
            label={C.title}
            hint={SP_HELP.purchaseOrders}
          />
        }
        description={C.description}
        aria-label={C.filtersAriaLabel}
      >
        <PurchaseOrdersFilters
          query={query}
          units={units}
          onPatch={patchQuery}
          onApply={() => {
            patchQuery({ page: 1 });
            setReloadKey((value) => value + 1);
          }}
          onClear={() => setQuery(createDefaultQuery(query.branch || defaultBranch))}
        />
      </SuppliesPageHero>

      {error ? (
        <div className="sp-purchase-orders__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      <SuppliesSectionCard title={C.listTitle} hint={C.listHint}>
        {loading ? <SuppliesLoadingCard title={C.loading} variant="panel" /> : null}

        {!loading && !error && items.length === 0 ? (
          <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <>
            <div className="sp-purchase-orders__meta">
              <span>{C.totalLabel(total)}</span>
              <div className="sp-purchase-orders__pager">
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  disabled={query.page <= 1}
                  onClick={() => patchQuery({ page: Math.max(1, query.page - 1) })}
                >
                  {C.prevPage}
                </SuppliesActionButton>
                <span>
                  {C.pageLabel} {query.page} / {totalPages}
                </span>
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  disabled={query.page >= totalPages}
                  onClick={() => patchQuery({ page: query.page + 1 })}
                >
                  {C.nextPage}
                </SuppliesActionButton>
              </div>
            </div>
            <div className="sp-purchase-orders__table-wrap">
              <table className="sp-purchase-orders__table">
                <thead>
                  <tr>
                    <th>{C.colPc}</th>
                    <th>{C.colItem}</th>
                    <th>{C.colProduct}</th>
                    <th>{C.colSupplier}</th>
                    <th>{C.colOpenQty}</th>
                    <th>{C.colDelivery}</th>
                    <th>{C.colStatus}</th>
                    <th>{C.colOpenValue}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const key = `${item.branch}-${item.order_number}-${item.order_item ?? ""}`;
                    const isSelected =
                      query.order === buildOrderKey(item.branch, item.order_number);
                    return (
                      <tr
                        key={key}
                        className={isSelected ? "is-selected" : undefined}
                        onClick={() => onSelectRow(item)}
                        onKeyDown={(event) => {
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            onSelectRow(item);
                          }
                        }}
                        tabIndex={0}
                        role="button"
                      >
                        <td>{item.order_number || "—"}</td>
                        <td>{item.order_item || "—"}</td>
                        <td>
                          {formatProductLabel(item.product_code, item.product_description)}
                        </td>
                        <td>{item.supplier_name || item.supplier_code || "—"}</td>
                        <td>{item.open_quantity ?? "—"}</td>
                        <td>{formatDatePtBr(item.expected_delivery_date)}</td>
                        <td>
                          <SuppliesStatusBadge
                            label={labelDeliveryStatus(item.delivery_status)}
                            variant={statusBadgeVariant(item.delivery_status)}
                          />
                        </td>
                        <td>{formatMoneyBr(item.open_value)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </SuppliesSectionCard>

      {selected ? (
        <SuppliesSectionCard
          title={
            selectedItem
              ? `${C.detailTitle} ${selectedItem.order_number}`
              : C.detailTitle
          }
          hint={C.detailHint}
          actions={
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={() => patchQuery({ order: "" })}
            >
              {C.detailClose}
            </SuppliesActionButton>
          }
        >
          <SuppliesStateBanner>{C.detailComingSoon}</SuppliesStateBanner>
          {selectedItem ? (
            <div className="sp-purchase-orders__detail-body">
              <dl>
                <div>
                  <dt>Filial</dt>
                  <dd>{selectedItem.branch}</dd>
                </div>
                <div>
                  <dt>Produto</dt>
                  <dd>
                    {formatProductLabel(
                      selectedItem.product_code,
                      selectedItem.product_description,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Fornecedor</dt>
                  <dd>{selectedItem.supplier_name || selectedItem.supplier_code || "—"}</dd>
                </div>
                <div>
                  <dt>Prometida</dt>
                  <dd>{formatDatePtBr(selectedItem.expected_delivery_date)}</dd>
                </div>
                <div>
                  <dt>Situação</dt>
                  <dd>{labelDeliveryStatus(selectedItem.delivery_status)}</dd>
                </div>
                <div>
                  <dt>Valor aberto</dt>
                  <dd>{formatMoneyBr(selectedItem.open_value)}</dd>
                </div>
              </dl>
            </div>
          ) : (
            <p>
              Pedido {selected.branch}:{selected.orderNumber} marcado na URL — não está na
              página atual.
            </p>
          )}
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
