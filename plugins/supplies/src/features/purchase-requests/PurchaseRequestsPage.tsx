import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";

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
  downloadPurchaseRequestsExport,
  getPurchaseRequest,
  listPurchaseRequests,
} from "./api";
import {
  mapPurchaseRequestsFetchError,
  PURCHASE_REQUESTS_CONTENT as C,
} from "./content";
import { PurchaseRequestsFilters } from "./PurchaseRequestsFilters";
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

export function PurchaseRequestsPage({ basePath }: PurchaseRequestsPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const defaultBranch = session.preferences?.defaultBranch || units[0] || "01";
  const canExport = session.capabilities.export;

  const [query, setQuery] = useState<PurchaseRequestsQuery>(() =>
    parseQueryFromSearch(readBrowserSearch(), defaultBranch),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<PurchaseRequestListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const [detail, setDetail] = useState<PurchaseRequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailNotFound, setDetailNotFound] = useState(false);

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
    listPurchaseRequests(query, controller.signal)
      .then((payload) => {
        setItems(payload.items ?? []);
        setTotal(payload.total ?? 0);
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

  const totalPages = Math.max(1, Math.ceil(total / query.page_size) || 1);
  const homeHref = buildPluginPath("home", basePath);
  const detailOpen = Boolean(detailTarget);

  const patchQuery = (patch: Partial<PurchaseRequestsQuery>) => {
    setQuery((current) => ({ ...current, ...patch }));
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
        actions={
          canExport ? (
            <SuppliesActionButton
              type="button"
              variant="ghost"
              title={C.exportTitle}
              onClick={onExport}
            >
              <Download size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
              {C.exportLabel}
            </SuppliesActionButton>
          ) : null
        }
        aria-label={C.filtersAriaLabel}
      >
        <PurchaseRequestsFilters
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
        <div className="sp-purchase-requests__error">
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
            <div className="sp-purchase-requests__meta">
              <span>{C.totalLabel(total)}</span>
              <div className="sp-purchase-requests__pager">
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
            <div className="sp-purchase-requests__table-wrap">
              <table className="sp-purchase-requests__table">
                <thead>
                  <tr>
                    <th>{C.colSc}</th>
                    <th>{C.colItem}</th>
                    <th>{C.colProduct}</th>
                    <th>{C.colRequester}</th>
                    <th>{C.colCc}</th>
                    <th>{C.colOpened}</th>
                    <th>{C.colStage}</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const key = `${item.branch}-${item.request_number}-${item.request_item ?? ""}`;
                    const selected =
                      query.request === buildRequestKey(item.branch, item.request_number);
                    return (
                      <tr
                        key={key}
                        className={selected ? "is-selected" : undefined}
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
                        <td>{formatRequestNumber(item.request_number)}</td>
                        <td>{item.request_item || "—"}</td>
                        <td>
                          {formatProductLabel(item.product_code, item.product_description)}
                        </td>
                        <td>{item.requester?.name || item.requester?.code || "—"}</td>
                        <td>
                          {item.cost_center?.code || item.cost_center_code || "—"}
                        </td>
                        <td>{formatDatePtBr(item.request_issue_date)}</td>
                        <td>{labelOverallStage(item.derived?.overall_stage)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        ) : null}
      </SuppliesSectionCard>

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
                  <dd>{detail.header.branch}</dd>
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
