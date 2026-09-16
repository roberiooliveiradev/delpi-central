import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildPurchaseRequestDetailPath,
} from "../../app/pluginRoutes";
import { canonicalizeUiBranches } from "../../app/suppliesUnits";
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
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  downloadPurchaseRequestsExport,
  listPurchaseRequests,
} from "./api";
import {
  mapPurchaseRequestsFetchError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import { PurchaseRequestsFilters } from "./PurchaseRequestsFilters";
import { PurchaseRequestsListTable } from "./PurchaseRequestsListTable";
import {
  authorizeQueryBranches,
  buildUrlSearch,
  createDefaultQuery,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";
import type { PurchaseRequestListItem, PurchaseRequestsQuery } from "./types";

type PurchaseRequestsPageProps = {
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

function sameBranches(left: readonly string[], right: readonly string[]): boolean {
  if (left.length !== right.length) return false;
  return left.every((code, index) => code === right[index]);
}

export function PurchaseRequestsPage({ basePath }: PurchaseRequestsPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const canExport = session.capabilities.export;

  const [query, setQuery] = useState<PurchaseRequestsQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), units),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<PurchaseRequestListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!units.length) return;
    setQuery((current) => {
      const nextBranches = canonicalizeUiBranches(current.branches, units);
      if (sameBranches(nextBranches, current.branches)) return current;
      return { ...current, branches: nextBranches };
    });
  }, [units]);

  useEffect(() => {
    const legacy = parseRequestKey(query.request);
    if (!legacy) return;
    navigatePluginPath(
      buildPurchaseRequestDetailPath(legacy.branch, legacy.requestNumber, basePath),
      { replace: true },
    );
  }, [basePath, query.request]);

  useEffect(() => {
    replaceBrowserSearch(buildUrlSearch(query));
  }, [query]);

  useEffect(() => {
    if (!units.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listPurchaseRequests(authorizeQueryBranches(query, units), controller.signal)
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
        setError(mapPurchaseRequestsFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, reloadKey, units]);

  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = useCallback((patch: Partial<PurchaseRequestsQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onClear = () => {
    setQuery(createDefaultQuery());
  };

  const onSelectRow = (item: PurchaseRequestListItem) => {
    navigatePluginPath(
      buildPurchaseRequestDetailPath(item.branch, item.request_number, basePath),
    );
  };

  const onExport = () => {
    if (!canExport) return;
    void downloadPurchaseRequestsExport(authorizeQueryBranches(query, units)).catch(
      (err: unknown) => {
        const message = err instanceof Error ? err.message : C.error;
        setError(mapPurchaseRequestsFetchError(message));
      },
    );
  };

  return (
    <div className="sp-page-stack sp-purchase-requests">
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
            hint={SP_HELP.purchaseRequests}
          />
        }
        description={C.description}
        aria-label={C.filtersAriaLabel}
        actions={
          <div className="sp-list-hero-actions sp-purchase-requests__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span
                className="sp-list-freshness sp-purchase-requests__freshness"
                title={SP_HELP.purchaseRequestsRefresh}
              >
                {C.updatedAtLabel(formatUpdatedAt(lastUpdatedAt))}
              </span>
            ) : null}
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading || !units.length}
              title={SP_HELP.purchaseRequestsRefresh}
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
          <PurchaseRequestsFilters
            query={query}
            units={units}
            onPatch={patchQuery}
            onClear={onClear}
          />
        )}
      </SuppliesPageHero>

      {error ? (
        <div className="sp-purchase-requests__error">
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
            <PurchaseRequestsListTable
              items={items}
              query={query}
              total={total}
              loading={loading}
              canExport={canExport}
              basePath={basePath}
              onExport={onExport}
              onPatchQuery={patchQuery}
              onSelectRow={onSelectRow}
            />
          ) : null}
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
