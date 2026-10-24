import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

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
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  getSafetyStockFilters,
  getSafetyStockSummary,
  listSafetyStockItems,
} from "./api";
import {
  SAFETY_STOCK_CONTENT as C,
  mapSafetyStockFetchError,
} from "./content";
import { SafetyStockFilters } from "./SafetyStockFilters";
import { SafetyStockListTable } from "./SafetyStockListTable";
import {
  buildUrlSearch,
  createDefaultQuery,
  formatQuantity,
  parseQueryFromSearch,
  sameSafetyStockQuery,
} from "./query";
import type {
  SafetyStockItem,
  SafetyStockQuery,
  SafetyStockSummary,
} from "./types";

type SafetyStockPageProps = {
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

export function SafetyStockPage({ basePath }: SafetyStockPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const historyWriteModeRef = useRef<HistoryWriteMode>("replace");

  const [query, setQuery] = useState<SafetyStockQuery>(() =>
    parseQueryFromSearch(readBrowserSearch()),
  );
  const [itemsLoading, setItemsLoading] = useState(true);
  const [itemsError, setItemsError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [filtersError, setFiltersError] = useState<string | null>(null);
  const [items, setItems] = useState<SafetyStockItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [summary, setSummary] = useState<SafetyStockSummary | null>(null);
  const [branchCatalog, setBranchCatalog] = useState<string[]>([]);
  const [productGroupOptions, setProductGroupOptions] = useState<string[]>([]);
  const [unitOptions, setUnitOptions] = useState<string[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  // Persistência de URL — F5/deep link restauram o recorte completo.
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
      const next = parseQueryFromSearch(readBrowserSearch());
      historyWriteModeRef.current = "skip";
      setQuery((current) => (sameSafetyStockQuery(current, next) ? current : next));
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  // Metadados de filtro (branch_catalog/grupos/UM) — uma vez por reload.
  useEffect(() => {
    const controller = new AbortController();
    getSafetyStockFilters(query.branch, query.includeBlocked, controller.signal)
      .then((payload) => {
        setBranchCatalog(payload.branch_catalog);
        setProductGroupOptions(payload.product_groups);
        setUnitOptions(payload.units);
        setFiltersError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : C.error;
        setFiltersError(mapSafetyStockFetchError(message));
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- branch/includeBlocked afetam as opções
  }, [query.branch, query.includeBlocked, reloadKey]);

  // Resumo — canal independente: falha não derruba a listagem.
  useEffect(() => {
    const controller = new AbortController();
    getSafetyStockSummary(query, controller.signal)
      .then((payload) => {
        setSummary(payload);
        setSummaryError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setSummary(null);
        const message = err instanceof Error ? err.message : C.error;
        setSummaryError(mapSafetyStockFetchError(message));
      })
    return () => controller.abort();
  }, [query, reloadKey]);

  // Listagem — paginação e ordenação server-side.
  useEffect(() => {
    const controller = new AbortController();
    setItemsLoading(true);
    listSafetyStockItems(query, controller.signal)
      .then((payload) => {
        setItems(payload.items);
        setTotal(payload.total);
        setTotalPages(
          typeof payload.total_pages === "number"
            ? payload.total_pages
            : Math.ceil(
                payload.total / Math.max(1, payload.page_size || query.page_size),
              ),
        );
        setItemsError(null);
        setLastUpdatedAt(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        const message = err instanceof Error ? err.message : C.error;
        setItemsError(mapSafetyStockFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setItemsLoading(false);
      });
    return () => controller.abort();
  }, [query, reloadKey]);

  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = useCallback((patch: Partial<SafetyStockQuery>) => {
    historyWriteModeRef.current = "push";
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onClear = () => {
    historyWriteModeRef.current = "push";
    setQuery(createDefaultQuery());
  };

  // Opções de filial: catálogo operacional do BFF; fallback = unidades da sessão.
  const branchOptions = branchCatalog.length ? branchCatalog : [...units];

  const highlights = useMemo(() => {
    // Indisponível (erro/null) nunca vira «0» — zero é um valor real do produtor.
    const unavailable = summary == null;
    const metric = (value: number | undefined) =>
      unavailable || value == null ? "—" : value.toLocaleString("pt-BR");
    return [
      {
        id: "total-materials",
        label: C.heroTotal,
        value: metric(summary?.total_materials),
      },
      {
        id: "with-safety-stock",
        label: C.heroWithSafetyStock,
        value: metric(summary?.with_safety_stock),
      },
      {
        id: "without-safety-stock",
        label: C.heroWithoutSafetyStock,
        value: metric(summary?.without_safety_stock),
      },
      {
        id: "below-safety-stock",
        label: C.heroBelow,
        value: metric(summary?.below_safety_stock),
        tone: "danger" as const,
      },
      {
        id: "at-safety-stock",
        label: C.heroAt,
        value: metric(summary?.at_safety_stock),
        tone: "warning" as const,
      },
      {
        id: "above-safety-stock",
        label: C.heroAbove,
        value: metric(summary?.above_safety_stock),
      },
    ];
  }, [summary]);

  const deficitByUnit = summary?.deficit_by_unit ?? [];
  const loading = itemsLoading;

  return (
    <div className="sp-page-stack sp-safety-stock">
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
          <SuppliesSectionHintLabel label={C.title} hint={SP_HELP.safetyStock} />
        }
        description={C.description}
        aria-label={C.filtersAriaLabel}
        highlights={highlights}
        actions={
          <div className="sp-list-hero-actions sp-safety-stock__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span
                className="sp-list-freshness sp-safety-stock__freshness"
                title={SP_HELP.safetyStockRefresh}
              >
                {C.updatedAtLabel(formatUpdatedAt(lastUpdatedAt))}
              </span>
            ) : null}
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading}
              title={SP_HELP.safetyStockRefresh}
            >
              <RefreshCw size={16} aria-hidden="true" />
              <span>{C.refreshAction}</span>
            </SuppliesActionButton>
          </div>
        }
      >
        {filtersError ? (
          <SuppliesStateBanner variant="error">
            {C.filtersUnavailable}
          </SuppliesStateBanner>
        ) : null}
        <SafetyStockFilters
          query={query}
          branchOptions={branchOptions}
          productGroupOptions={productGroupOptions}
          unitOptions={unitOptions}
          onPatch={patchQuery}
          onClear={onClear}
        />
      </SuppliesPageHero>

      {summaryError ? (
        <SuppliesStateBanner variant="error">
          {C.errorSummary}
        </SuppliesStateBanner>
      ) : null}

      {summary && !summaryError ? (
        <SuppliesSectionCard title={C.coverageTitle}>
          <ul
            className="sp-safety-stock__metrics"
            aria-label={C.coverageTitle}
          >
            <li>
              <span className="sp-safety-stock__metric-label">
                {C.coverageWithPrimary}
              </span>
              <span className="sp-safety-stock__metric-value">
                {summary.with_primary_stock.toLocaleString("pt-BR")}
              </span>
            </li>
            <li>
              <span className="sp-safety-stock__metric-label">
                {C.coverageWithoutPrimary}
              </span>
              <span className="sp-safety-stock__metric-value">
                {summary.without_primary_stock.toLocaleString("pt-BR")}
              </span>
            </li>
            <li>
              <span className="sp-safety-stock__metric-label">
                {C.coverageWorkInProcess}
              </span>
              <span className="sp-safety-stock__metric-value">
                {summary.with_work_in_process_stock.toLocaleString("pt-BR")}
              </span>
            </li>
          </ul>
          <div className="sp-safety-stock__deficit">
            <SuppliesSectionHintLabel
              label={C.deficitTitle}
              hint={SP_HELP.safetyStockDeficit}
            />
            {deficitByUnit.length ? (
              <ul className="sp-safety-stock__deficit-list">
                {deficitByUnit.map((row) => (
                  <li key={row.unit} className="sp-safety-stock__deficit-chip">
                    {C.deficitChip(
                      row.unit,
                      formatQuantity(row.deficit_quantity),
                      row.material_count,
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="sp-safety-stock__deficit-empty">{C.deficitEmpty}</p>
            )}
          </div>
        </SuppliesSectionCard>
      ) : null}

      {itemsError ? (
        <div className="sp-safety-stock__error">
          <SuppliesStateBanner variant="error">{itemsError}</SuppliesStateBanner>
          <SuppliesActionButton type="button" variant="primary" onClick={reload}>
            {C.retry}
          </SuppliesActionButton>
        </div>
      ) : null}

      <SuppliesSectionCard title={C.listTitle} hint={C.listHint}>
        {loading ? <SuppliesLoadingCard title={C.loading} variant="panel" /> : null}

        {!loading && !itemsError && items.length === 0 ? (
          <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage}>
            <div className="sp-safety-stock__empty-actions">
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

        {!loading && !itemsError && items.length > 0 ? (
          <SafetyStockListTable
            items={items}
            query={query}
            total={total}
            totalPages={totalPages}
            loading={loading}
            onPatchQuery={patchQuery}
          />
        ) : null}
      </SuppliesSectionCard>
    </div>
  );
}
