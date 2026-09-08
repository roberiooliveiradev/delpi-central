import { useEffect, useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { Download, ShoppingCart } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import {
  SuppliesEmptyState,
  SuppliesPagePath,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  downloadPurchaseRequestsExport,
  getPurchaseRequest,
  listPurchaseRequests,
} from "./api";
import { PURCHASE_REQUESTS_CONTENT as C } from "./content";
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
import type { OverallStage, PurchaseRequestDetail, PurchaseRequestListItem, PurchaseRequestsQuery } from "./types";
import { OVERALL_STAGE_VALUES } from "./types";

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
        setError(err instanceof Error ? err.message : C.error);
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
          setDetailError(message);
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
      setError(err instanceof Error ? err.message : C.error);
    });
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

      <header className="sp-purchase-requests__hero">
        <p className="sp-purchase-requests__eyebrow">
          <ShoppingCart size={16} strokeWidth={1.75} aria-hidden="true" />
          {C.eyebrow}
        </p>
        <h1>
          {C.title}{" "}
          <HelpTooltip content={SP_HELP.purchaseRequests} ariaLabel={C.helpAriaLabel} />
        </h1>
        <p className="sp-purchase-requests__description">{C.description}</p>
      </header>

      <form
        className="sp-purchase-requests__filters"
        onSubmit={(event) => {
          event.preventDefault();
          patchQuery({ page: 1 });
          setReloadKey((value) => value + 1);
        }}
      >
        <label>
          <span>{C.branchLabel}</span>
          <select
            value={query.branch}
            onChange={(event) => patchQuery({ branch: event.target.value, page: 1, request: "" })}
          >
            {units.map((unit) => (
              <option key={unit} value={unit}>
                {unit}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>{C.dateFromLabel}</span>
          <input
            type="date"
            value={query.date_from}
            onChange={(event) => patchQuery({ date_from: event.target.value, page: 1 })}
          />
        </label>
        <label>
          <span>{C.dateToLabel}</span>
          <input
            type="date"
            value={query.date_to}
            onChange={(event) => patchQuery({ date_to: event.target.value, page: 1 })}
          />
        </label>
        <label>
          <span>{C.requestNumberLabel}</span>
          <input
            value={query.request_number}
            onChange={(event) => patchQuery({ request_number: event.target.value, page: 1 })}
          />
        </label>
        <label>
          <span>{C.productLabel}</span>
          <input
            value={query.product_code}
            onChange={(event) => patchQuery({ product_code: event.target.value, page: 1 })}
          />
        </label>
        <label>
          <span>{C.stageLabel}</span>
          <select
            value={query.overall_stages[0] ?? ""}
            onChange={(event) => {
              const value = event.target.value as OverallStage | "";
              patchQuery({
                overall_stages: value ? [value] : [],
                page: 1,
              });
            }}
          >
            <option value="">{C.stageAll}</option>
            {OVERALL_STAGE_VALUES.map((stage) => (
              <option key={stage} value={stage}>
                {labelOverallStage(stage)}
              </option>
            ))}
          </select>
        </label>
        <div className="sp-purchase-requests__filter-actions">
          <button type="submit" className="sp-purchase-requests__btn">
            {C.applyFilters}
          </button>
          <button
            type="button"
            className="sp-purchase-requests__btn sp-purchase-requests__btn--ghost"
            onClick={() => setQuery(createDefaultQuery(query.branch || defaultBranch))}
          >
            {C.clearFilters}
          </button>
          {canExport ? (
            <button
              type="button"
              className="sp-purchase-requests__btn sp-purchase-requests__btn--ghost"
              title={C.exportTitle}
              onClick={onExport}
            >
              <Download size={16} strokeWidth={1.75} aria-hidden="true" />
              {C.exportLabel}
            </button>
          ) : null}
        </div>
      </form>

      {error ? (
        <div className="sp-purchase-requests__error">
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
          <button
            type="button"
            className="sp-purchase-requests__btn"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            {C.retry}
          </button>
        </div>
      ) : null}

      {loading ? <SuppliesStateBanner>{C.loading}</SuppliesStateBanner> : null}

      {!loading && !error && items.length === 0 ? (
        <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <>
          <div className="sp-purchase-requests__meta">
            <span>{C.totalLabel(total)}</span>
            <div className="sp-purchase-requests__pager">
              <button
                type="button"
                className="sp-purchase-requests__btn sp-purchase-requests__btn--ghost"
                disabled={query.page <= 1}
                onClick={() => patchQuery({ page: Math.max(1, query.page - 1) })}
              >
                {C.prevPage}
              </button>
              <span>
                {C.pageLabel} {query.page} / {totalPages}
              </span>
              <button
                type="button"
                className="sp-purchase-requests__btn sp-purchase-requests__btn--ghost"
                disabled={query.page >= totalPages}
                onClick={() => patchQuery({ page: query.page + 1 })}
              >
                {C.nextPage}
              </button>
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

      {detailOpen ? (
        <aside className="sp-purchase-requests__detail" aria-label={C.detailTitle}>
          <div className="sp-purchase-requests__detail-head">
            <h2>
              {detail?.header
                ? formatRequestNumber(detail.header.request_number)
                : C.detailTitle}
            </h2>
            <button
              type="button"
              className="sp-purchase-requests__btn sp-purchase-requests__btn--ghost"
              onClick={() => patchQuery({ request: "" })}
            >
              {C.detailClose}
            </button>
          </div>
          {detailLoading ? <SuppliesStateBanner>{C.detailLoading}</SuppliesStateBanner> : null}
          {!detailLoading && (detailError || detailNotFound) ? (
            <div className="sp-purchase-requests__error">
              <SuppliesStateBanner variant="error">
                {detailNotFound ? C.detailNotFound : detailError}
              </SuppliesStateBanner>
              <button
                type="button"
                className="sp-purchase-requests__btn"
                onClick={() => setReloadKey((value) => value + 1)}
              >
                {C.detailRetry}
              </button>
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
        </aside>
      ) : null}
    </div>
  );
}
