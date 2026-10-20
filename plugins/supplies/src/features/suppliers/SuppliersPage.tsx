import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";

import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildSupplierCreatePath,
  buildSupplierDetailPath,
} from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesCatalogSearchBar,
  SuppliesClearFiltersButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { ApiRequestError } from "../../api/httpClient";
import { listSuppliers } from "./api";
import { mapSuppliersFetchError, SUPPLIERS_CONTENT as C } from "./content";
import {
  buildUrlSearch,
  createDefaultQuery,
  hasActiveFilters,
  parseQueryFromSearch,
} from "./query";
import { SuppliersListTable } from "./SuppliersListTable";
import type { SupplierListItem, SuppliersQuery } from "./types";

type SuppliersPageProps = {
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

export function SuppliersPage({ basePath }: SuppliersPageProps) {
  const [query, setQuery] = useState<SuppliersQuery>(() =>
    parseQueryFromSearch(readBrowserSearch()),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<SupplierListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    replaceBrowserSearch(buildUrlSearch(query));
  }, [query]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listSuppliers(query, controller.signal)
      .then((payload) => {
        setItems(payload.items ?? []);
        setTotal(payload.total ?? 0);
        setTotalPages(payload.total_pages ?? 0);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        const message = err instanceof Error ? err.message : C.error;
        const code = err instanceof ApiRequestError ? err.code : undefined;
        setError(mapSuppliersFetchError(message, code));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, reloadKey]);

  const patchQuery = useCallback((patch: Partial<SuppliersQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onSelectRow = (item: SupplierListItem) => {
    navigatePluginPath(
      buildSupplierDetailPath(item.supplier_code, item.supplier_store, basePath),
    );
  };

  const homeHref = buildPluginPath("home", basePath);
  const forbidden = error === C.errorForbidden;

  return (
    <div className="sp-page-stack sp-suppliers">
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
          <SuppliesSectionHintLabel label={C.title} hint={SP_HELP.suppliers} />
        }
        description={C.description}
        actions={
          <div className="sp-list-hero-actions sp-suppliers__toolbar-actions">
            <SuppliesActionButton
              type="button"
              variant="primary"
              onClick={() =>
                navigatePluginPath(buildSupplierCreatePath(basePath))
              }
              title={SP_HELP.suppliersCreate}
            >
              <Plus size={16} aria-hidden="true" />
              <span>{C.newSupplierAction}</span>
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading}
              title={SP_HELP.suppliersRefresh}
            >
              <RefreshCw size={16} aria-hidden="true" />
              <span>{C.refreshAction}</span>
            </SuppliesActionButton>
          </div>
        }
      >
        <div className="sp-suppliers__filters" role="group" aria-label={C.searchLabel}>
          <SuppliesCatalogSearchBar
            value={query.query}
            onChange={(value) => patchQuery({ query: value, page: 1 })}
            onSelectHit={() => undefined}
            hits={[]}
            placeholder={C.searchPlaceholder}
            aria-label={C.searchLabel}
          />
          <SuppliesSelectField
            label={C.blockedLabel}
            hint={SP_HELP.suppliersBlocked}
            value={query.blocked}
            options={[
              { value: "0", label: C.blockedActive },
              { value: "1", label: C.blockedBlocked },
            ]}
            allowEmpty
            emptyLabel={C.blockedEmptyOption}
            onChange={(value) => patchQuery({ blocked: value, page: 1 })}
          />
          <SuppliesSelectField
            label={C.stateLabel}
            hint={SP_HELP.suppliersState}
            value={query.state}
            options={BRAZIL_STATES}
            allowEmpty
            emptyLabel="Todas"
            onChange={(value) => patchQuery({ state: value, page: 1 })}
          />
          {hasActiveFilters(query) ? (
            <SuppliesClearFiltersButton
              label={C.clearFilters}
              onClick={() => setQuery(createDefaultQuery())}
            />
          ) : null}
        </div>
      </SuppliesPageHero>

      {error ? (
        <div className="sp-suppliers__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          {!forbidden ? (
            <SuppliesActionButton type="button" variant="primary" onClick={reload}>
              {C.retry}
            </SuppliesActionButton>
          ) : null}
        </div>
      ) : null}

      <SuppliesSectionCard title={C.listTitle} hint={C.listHint}>
        {loading ? <SuppliesLoadingCard title={C.loading} variant="panel" /> : null}

        {!loading && !error && items.length === 0 ? (
          <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <SuppliersListTable
            items={items}
            query={query}
            total={total}
            totalPages={totalPages}
            onPatchQuery={patchQuery}
            onSelectRow={onSelectRow}
          />
        ) : null}
      </SuppliesSectionCard>
    </div>
  );
}

const BRAZIL_STATES: { value: string; label: string }[] = [
  { value: "ES", label: "ES" },
  { value: "SC", label: "SC" },
  { value: "AC", label: "AC" },
  { value: "AL", label: "AL" },
  { value: "AM", label: "AM" },
  { value: "AP", label: "AP" },
  { value: "BA", label: "BA" },
  { value: "CE", label: "CE" },
  { value: "DF", label: "DF" },
  { value: "GO", label: "GO" },
  { value: "MA", label: "MA" },
  { value: "MG", label: "MG" },
  { value: "MS", label: "MS" },
  { value: "MT", label: "MT" },
  { value: "PA", label: "PA" },
  { value: "PB", label: "PB" },
  { value: "PE", label: "PE" },
  { value: "PI", label: "PI" },
  { value: "PR", label: "PR" },
  { value: "RJ", label: "RJ" },
  { value: "RN", label: "RN" },
  { value: "RO", label: "RO" },
  { value: "RR", label: "RR" },
  { value: "RS", label: "RS" },
  { value: "SE", label: "SE" },
  { value: "SP", label: "SP" },
  { value: "TO", label: "TO" },
];
