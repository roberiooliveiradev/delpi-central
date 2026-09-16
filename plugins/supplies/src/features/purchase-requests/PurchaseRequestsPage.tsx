import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { formatSuppliesUnitLabel, resolveDefaultBranch } from "../../app/suppliesUnits";
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
  getPurchaseRequest,
  listPurchaseRequests,
} from "./api";
import {
  mapPurchaseRequestsFetchError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import { PurchaseRequestsFilters } from "./PurchaseRequestsFilters";
import { PurchaseRequestsListTable } from "./PurchaseRequestsListTable";
import {
  buildRequestKey,
  buildUrlSearch,
  createDefaultQuery,
  formatDatePtBr,
  formatProductLabel,
  formatRequestNumber,
  labelOverallStage,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";
import type { PurchaseRequestDetail, PurchaseRequestListItem, PurchaseRequestsQuery } from "./types";

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

export function PurchaseRequestsPage({ basePath }: PurchaseRequestsPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const defaultBranch = resolveDefaultBranch(units, session.preferences?.defaultBranch);
  const canExport = session.capabilities.export;

  const [query, setQuery] = useState<PurchaseRequestsQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), defaultBranch || units[0] || ""),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<PurchaseRequestListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

  const [detail, setDetail] = useState<PurchaseRequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailNotFound, setDetailNotFound] = useState(false);

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
    listPurchaseRequests(query, controller.signal)
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
  }, [query, reloadKey]);

  const detailTarget = useMemo(() => parseRequestKey(query.request), [query.request]);

  useEffect(() => {
    if (!detailTarget) {
      setDetail(null);
      setDetailError(null);
      setDetailNotFound(false);
      setDetailLoading(false);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    setDetailError(null);
    setDetailNotFound(false);
    getPurchaseRequest(
      detailTarget.branch,
      detailTarget.requestNumber,
      { date_from: query.date_from, date_to: query.date_to },
      controller.signal,
    )
      .then((payload) => setDetail(payload))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setDetail(null);
        const message = err instanceof Error ? err.message : C.detailError;
        if (/404|não encontrada|not found/i.test(message)) {
          setDetailNotFound(true);
          setDetailError(null);
        } else {
          setDetailError(mapPurchaseRequestsFetchError(message));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false);
      });
    return () => controller.abort();
  }, [detailTarget, query.date_from, query.date_to, reloadKey]);

  const homeHref = buildPluginPath("home", basePath);
  const detailOpen = Boolean(detailTarget);

  const patchQuery = useCallback((patch: Partial<PurchaseRequestsQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
  }, []);

  const reload = () => setReloadKey((value) => value + 1);

  const onClear = () => {
    const branch = defaultBranch || query.branch;
    setQuery(createDefaultQuery(branch));
  };

  const onSelectRow = (item: PurchaseRequestListItem) => {
    patchQuery({
      request: buildRequestKey(item.branch, item.request_number),
    });
  };

  const onExport = () => {
    if (!canExport) return;
    void downloadPurchaseRequestsExport(query).catch((err: unknown) => {
      const message = err instanceof Error ? err.message : C.error;
      setError(mapPurchaseRequestsFetchError(message));
    });
  };

  const detailTitle = detail?.header
    ? formatRequestNumber(detail.header.request_number)
    : C.detailTitle;

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

      {detailOpen ? (
        <SuppliesSectionCard
          title={detailTitle}
          hint={C.detailHint}
          actions={
            <SuppliesActionButton
              type="button"
              variant="ghost"
              onClick={() => patchQuery({ request: "" })}
            >
              {C.detailClose}
            </SuppliesActionButton>
          }
        >
          {detailLoading ? (
            <SuppliesLoadingCard title={C.detailLoading} variant="panel" />
          ) : null}
          {!detailLoading && (detailError || detailNotFound) ? (
            <div className="sp-purchase-requests__error">
              <SuppliesStateBanner variant="error">
                {detailNotFound ? C.detailNotFound : detailError}
              </SuppliesStateBanner>
              <SuppliesActionButton
                type="button"
                variant="primary"
                onClick={() => setReloadKey((value) => value + 1)}
              >
                {C.detailRetry}
              </SuppliesActionButton>
            </div>
          ) : null}
          {!detailLoading && detail ? (
            <div className="sp-purchase-requests__detail-body">
              <dl>
                <div>
                  <dt>Filial</dt>
                  <dd>{formatSuppliesUnitLabel(detail.header.branch)}</dd>
                </div>
                <div>
                  <dt>Solicitante</dt>
                  <dd>{detail.header.requester?.name || detail.header.requester?.code || "—"}</dd>
                </div>
                <div>
                  <dt>Abertura</dt>
                  <dd>{formatDatePtBr(detail.header.issue_date)}</dd>
                </div>
                <div>
                  <dt>Situação</dt>
                  <dd>{labelOverallStage(detail.header.overall_stage)}</dd>
                </div>
                <div>
                  <dt>Itens</dt>
                  <dd>{detail.header.visible_items_count ?? detail.lines.length}</dd>
                </div>
              </dl>
              <ul className="sp-purchase-requests__detail-lines">
                {detail.lines.map((line, index) => (
                  <li key={`${line.request_item ?? index}-${line.product_code ?? index}`}>
                    <strong>{line.request_item || "—"}</strong>{" "}
                    {formatProductLabel(line.product_code, line.product_description)}
                    <span>
                      {labelOverallStage(line.derived?.overall_stage)} · CC{" "}
                      {line.cost_center_code || "—"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}
