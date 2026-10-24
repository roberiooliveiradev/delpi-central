import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildSafetyStockDetailPath,
} from "../../app/pluginRoutes";
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
import {
  getSafetyStockFilters,
  getSafetyStockSummary,
  listSafetyStockItems,
} from "./api";
import {
  SAFETY_STOCK_CONTENT as C,
  mapSafetyStockFetchError,
} from "./content";
import { SafetyStockBranchChoiceDialog } from "./SafetyStockBranchChoiceDialog";
import { SafetyStockFilters } from "./SafetyStockFilters";
import { SafetyStockListTable } from "./SafetyStockListTable";
import {
  buildUrlSearch,
  createDefaultQuery,
  formatQuantity,
  normalizeBranchScope,
  parseDetailTargetFromSearch,
  parseQueryFromSearch,
  sameSafetyStockQuery,
} from "./query";
import { SAFETY_STOCK_ALL_SCOPE } from "./types";
import type {
  SafetyStockItem,
  SafetyStockQuery,
  SafetyStockSummary,
} from "./types";

type SafetyStockPageProps = {
  basePath: string;
};

type HistoryWriteMode = "replace" | "push" | "skip";

type ItemsLoadState = {
  key: string;
  status: "loading" | "ready" | "error";
  items: SafetyStockItem[];
  total: number;
  totalPages: number;
  error: string | null;
};

function itemsLoadingState(key: string): ItemsLoadState {
  return { key, status: "loading", items: [], total: 0, totalPages: 0, error: null };
}

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

/** Remove `item`/`itemBranch` de deep links legados (E11.S3) da query. */
function stripLegacyDetailParams(search: string): string {
  const params = new URLSearchParams(
    search.startsWith("?") ? search.slice(1) : search,
  );
  params.delete("item");
  params.delete("itemBranch");
  return params.toString();
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
  // E11.S7 — linha consolidada (`branch=all`) pede escolha explícita de filial
  // antes de navegar para a página de detalhe. Guarda só o código do material.
  const [branchChoiceCode, setBranchChoiceCode] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [filtersError, setFiltersError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SafetyStockSummary | null>(null);
  const [branchCatalog, setBranchCatalog] = useState<string[]>([]);
  const [productGroupOptions, setProductGroupOptions] = useState<string[]>([]);
  const [unitOptions, setUnitOptions] = useState<string[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const [itemsState, setItemsState] = useState<ItemsLoadState>(() =>
    itemsLoadingState(""),
  );

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
      const search = readBrowserSearch();
      const next = parseQueryFromSearch(search);
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

  // Listagem — paginação e ordenação server-side. Estado chaveado pelo
  // recorte: troca de filtro nunca exibe itens da consulta anterior.
  const itemsKey = useMemo(
    () => JSON.stringify([query, reloadKey]),
    [query, reloadKey],
  );
  useEffect(() => {
    const controller = new AbortController();
    listSafetyStockItems(query, controller.signal)
      .then((payload) => {
        setItemsState({
          key: itemsKey,
          status: "ready",
          items: payload.items,
          total: payload.total,
          totalPages:
            typeof payload.total_pages === "number"
              ? payload.total_pages
              : Math.ceil(
                  payload.total /
                    Math.max(1, payload.page_size || query.page_size),
                ),
          error: null,
        });
        setLastUpdatedAt(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : C.error;
        setItemsState({
          ...itemsLoadingState(itemsKey),
          status: "error",
          error: mapSafetyStockFetchError(message),
        });
      });
    return () => controller.abort();
  }, [query, reloadKey, itemsKey]);

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

  // Deep links legados (E11.S3: ?item=..&itemBranch=..) redirecionam para a
  // rota canônica de detalhe, preservando o recorte da listagem em `?from=`.
  useEffect(() => {
    const legacy = parseDetailTargetFromSearch(readBrowserSearch());
    if (!legacy) return;
    const rest = stripLegacyDetailParams(readBrowserSearch());
    navigatePluginPath(
      buildSafetyStockDetailPath(
        legacy.branch,
        legacy.productCode,
        basePath,
        rest ? `?from=${encodeURIComponent(rest)}` : undefined,
      ),
      { replace: true },
    );
  }, [basePath]);

  // Navega para a página de detalhe carregando o recorte atual da listagem —
  // «Voltar» restaura filtros/ordenação/página exatos (inclui `branch=all`).
  const navigateToDetail = useCallback(
    (productCode: string, branch: string) => {
      const listSearch = stripLegacyDetailParams(readBrowserSearch());
      navigatePluginPath(
        buildSafetyStockDetailPath(
          branch,
          productCode,
          basePath,
          listSearch ? `?from=${encodeURIComponent(listSearch)}` : undefined,
        ),
      );
    },
    [basePath],
  );

  // E11.S7 — filial concreta abre direto; consolidada (`all`) exige escolha
  // explícita, sem consulta de detalhe antes da seleção.
  const onOpenDetail = useCallback(
    (row: SafetyStockItem) => {
      const productCode = String(row.product_code ?? "").trim();
      if (!productCode) return;
      const branch = normalizeBranchScope(row.branch);
      if (branch === SAFETY_STOCK_ALL_SCOPE) {
        setBranchChoiceCode(productCode);
        return;
      }
      navigateToDetail(productCode, branch);
    },
    [navigateToDetail],
  );

  const onPickDetailBranch = useCallback(
    (branch: string) => {
      const productCode = branchChoiceCode;
      setBranchChoiceCode(null);
      if (!productCode) return;
      const normalized = normalizeBranchScope(branch);
      if (normalized === SAFETY_STOCK_ALL_SCOPE) return;
      navigateToDetail(productCode, normalized);
    },
    [branchChoiceCode, navigateToDetail],
  );

  // E11.S8 — filtros rápidos = o próprio `query.status` (fonte única):
  // chips e select Status são duas visões do mesmo estado; sem contadores
  // (o resumo do produtor já é limitado ao filtro ativo).
  const selectStatus = (status: SafetyStockQuery["status"]) => () =>
    patchQuery({ status, page: 1 });
  const statusChips = [
    {
      id: "all",
      label: C.chipAll,
      active: query.status === "",
      onSelect: selectStatus(""),
    },
    {
      id: "below",
      label: C.chipBelow,
      active: query.status === "below_safety_stock",
      onSelect: selectStatus("below_safety_stock"),
    },
    {
      id: "at",
      label: C.chipAt,
      active: query.status === "at_safety_stock",
      onSelect: selectStatus("at_safety_stock"),
    },
    {
      id: "above",
      label: C.chipAbove,
      active: query.status === "above_safety_stock",
      onSelect: selectStatus("above_safety_stock"),
    },
    {
      id: "without",
      label: C.chipWithout,
      active: query.status === "without_safety_stock",
      onSelect: selectStatus("without_safety_stock"),
    },
  ];

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

  const itemsView =
    itemsState.key === itemsKey ? itemsState : itemsLoadingState(itemsKey);
  const loading = itemsView.status === "loading";
  const itemsError = itemsView.status === "error" ? itemsView.error : null;
  const items = itemsView.items;
  const total = itemsView.total;
  const totalPages = itemsView.totalPages;

  const deficitByUnit = summary?.deficit_by_unit ?? [];

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
        <div className="sp-safety-stock__chip-row">
          <SuppliesScopeChipBar
            aria-label={C.quickFiltersAriaLabel}
            label={
              <SuppliesSectionHintLabel
                label={C.quickFiltersLabel}
                hint={SP_HELP.safetyStockQuickFilters}
              />
            }
            chips={statusChips}
          />
        </div>
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
            onOpenDetail={onOpenDetail}
          />
        ) : null}
      </SuppliesSectionCard>

      <SafetyStockBranchChoiceDialog
        productCode={branchChoiceCode}
        branches={branchOptions}
        onPick={onPickDetailBranch}
        onClose={() => setBranchChoiceCode(null)}
      />
    </div>
  );
}
