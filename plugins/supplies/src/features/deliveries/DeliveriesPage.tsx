import { useCallback, useEffect, useMemo, useState } from "react";
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
  SuppliesSectionHintLabel,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { listLateDeliveries } from "./api";
import { DELIVERIES_CONTENT as C, mapDeliveriesFetchError } from "./content";
import { DeliveriesFilters } from "./DeliveriesFilters";
import { DeliveriesListTable } from "./DeliveriesListTable";
import {
  buildUrlSearch,
  createDefaultQuery,
  parseQueryFromSearch,
} from "./query";
import type {
  DeliveriesQuery,
  DeliveryLateListItem,
  DeliveryLateSummary,
} from "./types";

type DeliveriesPageProps = {
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

function isDeliveryLateSummary(value: unknown): value is DeliveryLateSummary {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row.total_lines === "number" &&
    typeof row.late_lines === "number" &&
    typeof row.on_time_lines === "number"
  );
}

function sameBranches(left: readonly string[], right: readonly string[]): boolean {
  if (left.length !== right.length) return false;
  return left.every((code, index) => code === right[index]);
}

export function DeliveriesPage({ basePath }: DeliveriesPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;

  const [query, setQuery] = useState<DeliveriesQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), units),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<DeliveryLateListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [summary, setSummary] = useState<DeliveryLateSummary | null>(null);
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
    replaceBrowserSearch(buildUrlSearch(query));
  }, [query]);

  useEffect(() => {
    if (!units.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listLateDeliveries(query, controller.signal)
      .then((payload) => {
        setItems(payload.items ?? []);
        setTotal(payload.total ?? 0);
        setTotalPages(
          typeof payload.total_pages === "number"
            ? payload.total_pages
            : Math.ceil((payload.total ?? 0) / Math.max(1, payload.page_size || query.page_size)),
        );
        setSummary(isDeliveryLateSummary(payload.summary) ? payload.summary : null);
        setLastUpdatedAt(new Date());
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setSummary(null);
        const message = err instanceof Error ? err.message : C.error;
        setError(mapDeliveriesFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query, reloadKey, units]);

  const homeHref = buildPluginPath("home", basePath);

  const patchQuery = useCallback((patch: Partial<DeliveriesQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onClear = () => {
    setQuery(createDefaultQuery());
  };

  const highlights = useMemo(() => {
    const late = summary?.late_lines ?? 0;
    return [
      {
        id: "total-lines",
        label: C.heroTotal,
        value:
          summary == null ? "—" : summary.total_lines.toLocaleString("pt-BR"),
      },
      {
        id: "late-lines",
        label: C.heroLate,
        value: summary == null ? "—" : late.toLocaleString("pt-BR"),
        tone: summary != null && late > 0 ? ("warning" as const) : undefined,
      },
      {
        id: "on-time-lines",
        label: C.heroOnTime,
        value:
          summary == null
            ? "—"
            : summary.on_time_lines.toLocaleString("pt-BR"),
      },
    ];
  }, [summary]);

  return (
    <div className="sp-page-stack sp-deliveries">
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
            hint={SP_HELP.deliveries}
          />
        }
        description={C.description}
        aria-label={C.filtersAriaLabel}
        highlights={highlights}
        actions={
          <div className="sp-list-hero-actions sp-deliveries__toolbar-actions">
            {lastUpdatedAt && !loading ? (
              <span
                className="sp-list-freshness sp-deliveries__freshness"
                title={SP_HELP.deliveriesRefresh}
              >
                {C.updatedAtLabel(formatUpdatedAt(lastUpdatedAt))}
              </span>
            ) : null}
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={reload}
              disabled={loading || !units.length}
              title={SP_HELP.deliveriesRefresh}
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
          <DeliveriesFilters
            query={query}
            units={units}
            onPatch={patchQuery}
            onClear={onClear}
          />
        )}
      </SuppliesPageHero>

      {error ? (
        <div className="sp-deliveries__error">
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
            <DeliveriesListTable
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
