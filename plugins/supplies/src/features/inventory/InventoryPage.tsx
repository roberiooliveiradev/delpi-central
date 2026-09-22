import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { canonicalizeUiBranches } from "../../app/suppliesUnits";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import {
  getInventoryStockBalancesSummary,
  listInventoryStockBalances,
} from "./api";
import { INVENTORY_CONTENT as C, mapInventoryFetchError } from "./content";
import { InventoryFilters } from "./InventoryFilters";
import { InventoryListTable } from "./InventoryListTable";
import {
  buildUrlSearch,
  buildWarehouseFilterOptions,
  createDefaultQuery,
  formatMoneyBr,
  parseQueryFromSearch,
  sameInventoryQuery,
} from "./query";
import type {
  InventoryByWarehouse,
  InventoryQuery,
  InventoryStockItem,
  InventoryStockSummary,
} from "./types";
import { EMPTY_INVENTORY_SUMMARY } from "./types";

type InventoryPageProps = {
  basePath: string;
};

type HistoryWriteMode = "replace" | "push" | "skip";

function readBrowserSearch(): string {
  if (typeof window === "undefined") return "";
  return window.location.search || "";
}

function writeBrowserSearch(search: string, mode: Exclude<HistoryWriteMode, "skip">) {
  if (typeof window === "undefined") return;
  const next = `${window.location.pathname}${search}`;
  const current = `${window.location.pathname}${window.location.search || ""}`;
  if (next === current) return;
  if (mode === "push") {
    window.history.pushState(window.history.state, "", next);
    return;
  }
  window.history.replaceState(window.history.state, "", next);
}

function formatUpdatedAt(value: Date): string {
  return value.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isInventorySummary(value: unknown): value is InventoryStockSummary {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row.product_count === "number" &&
    typeof row.warehouse_count === "number" &&
    typeof row.total_stock_value === "number"
  );
}

function sameBranches(left: readonly string[], right: readonly string[]): boolean {
  if (left.length !== right.length) return false;
  return left.every((code, index) => code === right[index]);
}

export function InventoryPage({ basePath }: InventoryPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const historyWriteModeRef = useRef<HistoryWriteMode>("replace");

  const [query, setQuery] = useState<InventoryQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), units),
  );
  const [itemsLoading, setItemsLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<InventoryStockItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [summary, setSummary] = useState<InventoryStockSummary | null>(null);
  const [catalogByWarehouse, setCatalogByWarehouse] = useState<
    InventoryByWarehouse[]
  >([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!units.length) return;
    setQuery((current) => {
      const nextBranches = canonicalizeUiBranches(current.branches, units);
      if (sameBranches(nextBranches, current.branches)) return current;
      historyWriteModeRef.current = "replace";
      return { ...current, branches: nextBranches, page: 1 };
    });
  }, [units]);

  useEffect(() => {
    const mode = historyWriteModeRef.current;
    if (mode === "skip") {
      historyWriteModeRef.current = "push";
      return;
    }
    writeBrowserSearch(buildUrlSearch(query), mode);
    historyWriteModeRef.current = "push";
  }, [query]);

  useEffect(() => {
    const onPopState = () => {
      const next = parseQueryFromSearch(readBrowserSearch(), units);
      historyWriteModeRef.current = "skip";
      setQuery((current) => (sameInventoryQuery(current, next) ? current : next));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, [units]);

  // Catalog summary without warehouse — warehouse options stay stable when filtering.
  useEffect(() => {
    if (!units.length) return;
    const controller = new AbortController();
    getInventoryStockBalancesSummary(
      { branches: query.branches, warehouse: "" },
      controller.signal,
      { includeWarehouse: false },
    )
      .then((payload) => {
        setCatalogByWarehouse(
          Array.isArray(payload.by_warehouse) ? payload.by_warehouse : [],
        );
        if (!query.warehouse.trim() && isInventorySummary(payload.summary)) {
          setSummary(payload.summary);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (!query.warehouse.trim()) {
          setCatalogByWarehouse([]);
          setSummary(null);
          const message = err instanceof Error ? err.message : C.error;
          setError(mapInventoryFetchError(message));
        }
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- catalog keyed by branch scope only
  }, [query.branches, units, reloadKey]);

  // Filtered summary (when warehouse selected) + items page.
  useEffect(() => {
    if (!units.length) return;
    const controller = new AbortController();
    setItemsLoading(true);
    setSummaryLoading(true);
    setError(null);

    const summaryPromise = query.warehouse.trim()
      ? getInventoryStockBalancesSummary(query, controller.signal)
      : Promise.resolve(null);

    Promise.all([
      summaryPromise,
      listInventoryStockBalances(query, controller.signal),
    ])
      .then(([summaryPayload, itemsPayload]) => {
        if (summaryPayload && isInventorySummary(summaryPayload.summary)) {
          setSummary(summaryPayload.summary);
        }
        setItems(itemsPayload.items ?? []);
        setTotal(itemsPayload.total ?? 0);
        setTotalPages(
          typeof itemsPayload.total_pages === "number"
            ? itemsPayload.total_pages
            : Math.ceil(
                (itemsPayload.total ?? 0) /
                  Math.max(1, itemsPayload.page_size || query.page_size),
              ),
        );
        setLastUpdatedAt(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        if (query.warehouse.trim()) setSummary(null);
        const message = err instanceof Error ? err.message : C.error;
        setError(mapInventoryFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setItemsLoading(false);
          setSummaryLoading(false);
        }
      });

    return () => controller.abort();
  }, [query, reloadKey, units]);

  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = useCallback((patch: Partial<InventoryQuery>) => {
    historyWriteModeRef.current = "push";
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onClear = () => {
    historyWriteModeRef.current = "push";
    setQuery(createDefaultQuery());
  };

  const warehouseOptions = useMemo(
    () => buildWarehouseFilterOptions(catalogByWarehouse),
    [catalogByWarehouse],
  );

  const heroSummary = summary ?? EMPTY_INVENTORY_SUMMARY;
  const highlights = useMemo(() => {
    const loadingHero = summary == null || (summaryLoading && Boolean(query.warehouse));
    return [
      {
        id: "product-count",
        label: C.heroProducts,
        value: loadingHero
          ? "—"
          : heroSummary.product_count.toLocaleString("pt-BR"),
      },
      {
        id: "warehouse-count",
        label: C.heroWarehouses,
        value: loadingHero
          ? "—"
          : heroSummary.warehouse_count.toLocaleString("pt-BR"),
      },
      {
        id: "total-stock-value",
        label: C.heroStockValue,
        value: loadingHero ? "—" : formatMoneyBr(heroSummary.total_stock_value),
      },
    ];
  }, [heroSummary, query.warehouse, summary, summaryLoading]);

  const loading = itemsLoading;

  return (
    <div className="sp-page-stack sp-inventory">
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
        title={C.title}
        description={C.description}
        aria-label={C.filtersAriaLabel}
        highlights={highlights}
        actions={
          <div className="sp-list-hero-actions sp-inventory__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span className="sp-list-freshness sp-inventory__freshness">
                {C.updatedAtLabel(formatUpdatedAt(lastUpdatedAt))}
              </span>
            ) : null}
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading || !units.length}
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
          <InventoryFilters
            query={query}
            units={units}
            warehouseOptions={warehouseOptions}
            onPatch={patchQuery}
            onClear={onClear}
          />
        )}
      </SuppliesPageHero>

      {error ? (
        <div className="sp-inventory__error">
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
            <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage}>
              <div className="sp-inventory__empty-actions">
                <SuppliesActionButton type="button" variant="ghost" onClick={onClear}>
                  {C.emptyClearAction}
                </SuppliesActionButton>
                <SuppliesActionButton
                  type="button"
                  variant="primary"
                  onClick={() => navigatePluginView("help", { basePath })}
                >
                  {C.emptyHelpAction}
                </SuppliesActionButton>
              </div>
            </SuppliesEmptyState>
          ) : null}

          {!loading && !error && items.length > 0 ? (
            <InventoryListTable
              items={items}
              query={query}
              total={total}
              totalPages={totalPages}
              loading={loading}
              onPatchQuery={patchQuery}
            />
          ) : null}
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
