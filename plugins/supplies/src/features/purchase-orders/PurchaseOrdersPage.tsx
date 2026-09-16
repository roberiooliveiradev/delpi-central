import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath, buildPurchaseOrderDetailPath } from "../../app/pluginRoutes";
import { resolveDefaultBranch } from "../../app/suppliesUnits";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesScopeChipBar,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { listPurchaseOrders } from "./api";
import {
  mapPurchaseOrdersFetchError,
  PURCHASE_ORDERS_CONTENT as C,
} from "./content";
import { PurchaseOrdersFilters } from "./PurchaseOrdersFilters";
import { PurchaseOrdersListTable } from "./PurchaseOrdersListTable";
import {
  buildUrlSearch,
  createDefaultQuery,
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

function formatUpdatedAt(value: Date): string {
  return value.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function PurchaseOrdersPage({ basePath }: PurchaseOrdersPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const defaultBranch = resolveDefaultBranch(units, session.preferences?.defaultBranch);

  const [query, setQuery] = useState<PurchaseOrdersQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), defaultBranch || units[0] || ""),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<PurchaseOrderListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!units.length) return;
    if (!units.includes(query.branch)) {
      setQuery((current) => ({
        ...current,
        branch: defaultBranch || units[0],
        page: 1,
      }));
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
        setLastUpdatedAt(new Date());
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

  useEffect(() => {
    const selected = parseOrderKey(query.order);
    if (!selected) return;
    navigatePluginPath(
      buildPurchaseOrderDetailPath(selected.branch, selected.orderNumber, basePath),
      { replace: true },
    );
  }, [basePath, query.order]);

  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = useCallback((patch: Partial<PurchaseOrdersQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onSelectRow = (item: PurchaseOrderListItem) => {
    navigatePluginPath(buildPurchaseOrderDetailPath(item.branch, item.order_number, basePath));
  };

  const onClear = () => {
    const branch = defaultBranch || query.branch;
    setQuery(createDefaultQuery(branch));
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
        actions={
          <div className="sp-list-hero-actions sp-purchase-orders__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span
                className="sp-list-freshness sp-purchase-orders__freshness"
                title={SP_HELP.purchaseOrdersRefresh}
              >
                {C.updatedAtLabel(formatUpdatedAt(lastUpdatedAt))}
              </span>
            ) : null}
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading || !units.length}
              title={SP_HELP.purchaseOrdersRefresh}
            >
              <RefreshCw size={16} aria-hidden="true" />
              <span>{C.refreshAction}</span>
            </SuppliesActionButton>
          </div>
        }
      >
        {!units.length ? (
          <SuppliesEmptyState title={C.noUnitsTitle} message={C.noUnitsMessage} />
        ) : (
          <>
            <div className="sp-purchase-orders__chip-row">
              <SuppliesScopeChipBar
                aria-label={C.attentionAriaLabel}
                label={C.attentionLabel}
                chips={[
                  {
                    id: "all",
                    label: C.attentionAll,
                    active: !query.late_only,
                    onSelect: () => patchQuery({ late_only: false, page: 1 }),
                  },
                  {
                    id: "late",
                    label: C.attentionLate,
                    active: query.late_only,
                    onSelect: () => patchQuery({ late_only: true, page: 1 }),
                  },
                ]}
              />
            </div>
            <PurchaseOrdersFilters
              query={query}
              units={units}
              onPatch={patchQuery}
              onClear={onClear}
            />
          </>
        )}
      </SuppliesPageHero>

      {error ? (
        <div className="sp-purchase-orders__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          <SuppliesActionButton type="button" variant="primary" onClick={reload}>
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      {units.length ? (
        <SuppliesSectionCard title={C.listTitle} hint={C.listHint}>
          {loading ? <SuppliesLoadingCard title={C.loading} variant="panel" /> : null}

          {!loading && !error && items.length === 0 ? (
            <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
          ) : null}

          {!loading && !error && items.length > 0 ? (
            <PurchaseOrdersListTable
              items={items}
              query={query}
              total={total}
              loading={loading}
              basePath={basePath}
              onPatchQuery={patchQuery}
              onSelectRow={onSelectRow}
            />
          ) : null}
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
