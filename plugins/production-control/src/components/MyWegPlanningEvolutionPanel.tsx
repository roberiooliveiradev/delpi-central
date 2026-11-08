import {
  createDashboardKpiCard,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import {
  ArrowRight,
  CalendarClock,
  Eraser,
  Filter,
  LogIn,
  LogOut,
  Package,
  Search,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { fetchMyWegNeedBatchesCompare } from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type {
  MyWegCompareIndicativeProduct,
  MyWegComparePayload,
  MyWegNeedsBatchSummary,
} from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import { deltaToneClass, movementBadgeClass } from "../utils/mywegSemanticTone";
import {
  resolveMyWegCompareAnalysis,
  type MyWegCompareAnalysis,
} from "../utils/routeParser";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { MyWegProbableDateShiftsSection } from "./MyWegProbableDateShiftsSection";
import { MyWegProductConsolidationPanel } from "./MyWegProductConsolidationPanel";

type Props = {
  historyItems: MyWegNeedsBatchSummary[];
  selectedBatchId: string | null;
  analysis?: MyWegCompareAnalysis | null;
  onAnalysisChange?: (analysis: MyWegCompareAnalysis) => void;
  /** Quando true, omite o hub interno remessa/produto (abas principais na page). */
  hideAnalysisHub?: boolean;
};

const texts = copy.mywegNeeds.evolution;
const PAGE_SIZE = 50;

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

function movementLabel(movement: string): string {
  switch (movement) {
    case "increased":
      return texts.movement.increased;
    case "decreased":
      return texts.movement.decreased;
    case "appeared":
      return texts.movement.appeared;
    case "disappeared":
      return texts.movement.disappeared;
    case "unchanged":
      return texts.movement.unchanged;
    default:
      return movement;
  }
}

function pickDefaultPair(
  historyItems: MyWegNeedsBatchSummary[],
  selectedBatchId: string | null,
): { fromId: string; toId: string } {
  if (historyItems.length < 2) {
    return { fromId: "", toId: "" };
  }
  const to =
    historyItems.find((item) => item.id === selectedBatchId) ?? historyItems[0];
  const toDay = to.collectionDate;
  const fromDistinct = historyItems.find(
    (item) => item.id !== to.id && item.collectionDate !== toDay,
  );
  if (fromDistinct) {
    return { fromId: fromDistinct.id, toId: to.id };
  }
  return { fromId: "", toId: to.id };
}

function formatQty(value: string | null | undefined): string {
  if (value == null || value === "") return "—";
  return formatDecimalString(value);
}

function formatRemessaBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
}

export function MyWegPlanningEvolutionPanel({
  historyItems,
  selectedBatchId,
  analysis,
  onAnalysisChange,
  hideAnalysisHub = false,
}: Props) {
  const activeAnalysis = resolveMyWegCompareAnalysis(analysis);
  const [fromId, setFromId] = useState<string>("");
  const [toId, setToId] = useState<string>("");
  const [billingMode, setBillingMode] = useState<"none" | "indicative">("none");
  const [searchDraft, setSearchDraft] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [payload, setPayload] = useState<MyWegComparePayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);

  useEffect(() => {
    const pair = pickDefaultPair(historyItems, selectedBatchId);
    setFromId(pair.fromId);
    setToId(pair.toId);
    setPage(1);
    setSearch("");
    setSearchDraft("");
  }, [historyItems, selectedBatchId]);

  useEffect(() => {
    setPage(1);
  }, [fromId, toId, billingMode, search]);

  useEffect(() => {
    if (activeAnalysis !== "remessa") {
      setPayload(null);
      setLoading(false);
      setError(null);
      setStatus(null);
      return;
    }
    if (!fromId || !toId || fromId === toId) {
      setPayload(null);
      if (fromId && toId && fromId === toId) {
        setError(texts.chronoInvalid);
        setStatus(422);
      }
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setStatus(null);
    void fetchMyWegNeedBatchesCompare({
      fromBatchId: fromId,
      toBatchId: toId,
      billingMode,
      search,
      page,
      pageSize: PAGE_SIZE,
      changesOnly: true,
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) setPayload(data);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setPayload(null);
        setStatus(httpErrorStatus(err));
        setError(err instanceof Error ? err.message : texts.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [activeAnalysis, fromId, toId, billingMode, search, page]);

  const columns = useMemo<DataTableColumn<MyWegComparePayload["items"][number]>[]>(
    () => [
      {
        key: "product",
        header: texts.columns.product,
        render: (row) =>
          row.verifiedProductCode || row.materialWegTratado || row.productKey || "—",
      },
      {
        key: "remessa",
        header: texts.columns.remessa,
        render: (row) => formatRemessaBr(row.remessa),
      },
      {
        key: "movement",
        header: texts.columns.movement,
        render: (row) => {
          const label = movementLabel(row.movement);
          const text = row.inHorizon14d ? `${label} · ${texts.horizonBadge}` : label;
          return <span className={movementBadgeClass(row.movement)}>{text}</span>;
        },
      },
      {
        key: "prev",
        header: texts.columns.previous,
        align: "right",
        render: (row) => formatDecimalString(row.previousQuantityUn),
      },
      {
        key: "curr",
        header: texts.columns.current,
        align: "right",
        render: (row) => formatDecimalString(row.currentQuantityUn),
      },
      {
        key: "delta",
        header: texts.columns.delta,
        align: "right",
        render: (row) => (
          <span className={deltaToneClass(row.movement)}>
            {formatDecimalString(row.deltaQuantityUn)}
          </span>
        ),
      },
    ],
    [],
  );

  const indicativeColumns = useMemo<DataTableColumn<MyWegCompareIndicativeProduct>[]>(
    () => [
      {
        key: "product",
        header: texts.columns.product,
        render: (row) => row.productCode,
      },
      {
        key: "unit",
        header: texts.columns.unit,
        render: (row) => row.unit || "—",
      },
      {
        key: "candidate",
        header: texts.columns.candidate,
        align: "right",
        render: (row) => formatQty(row.candidateQuantityUn),
      },
      {
        key: "fiscalOrigin",
        header: texts.columns.fiscalOrigin,
        render: (row) => {
          if (row.originalFiscalLabel) return row.originalFiscalLabel;
          if (row.originalQuantity != null && row.originalUnit) {
            return `${formatDecimalString(row.originalQuantity)} ${row.originalUnit}`;
          }
          return "—";
        },
      },
      {
        key: "prevNeed",
        header: texts.columns.previousNeed,
        align: "right",
        render: (row) => formatDecimalString(row.previousNeedUn),
      },
      {
        key: "currNeed",
        header: texts.columns.currentNeed,
        align: "right",
        render: (row) => formatDecimalString(row.currentNeedUn),
      },
      {
        key: "abated",
        header: texts.columns.abated,
        align: "right",
        render: (row) => formatQty(row.hypotheticallyAbatedUn),
      },
      {
        key: "fifo",
        header: texts.columns.fifoBalance,
        align: "right",
        render: (row) => formatQty(row.fifoExpectedBalanceUn),
      },
      {
        key: "residual",
        header: texts.columns.residual,
        align: "right",
        render: (row) => formatQty(row.residualVsCurrentUn),
      },
    ],
    [],
  );

  const applySearch = () => setSearch(searchDraft.trim());
  const clearSearch = () => {
    setSearchDraft("");
    setSearch("");
  };

  if (historyItems.length < 2) {
    return (
      <section className="ppc-myweg-needs__evolution" aria-label={texts.title}>
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.insufficient}
        </p>
      </section>
    );
  }

  const summary = payload?.observed.summary;
  const billing = payload?.billing;
  const indicativeRows = billing?.indicativeProducts ?? [];
  const showBillingTable =
    billingMode === "indicative" &&
    billing != null &&
    billing.status !== "skipped" &&
    billing.status !== "unavailable" &&
    indicativeRows.length > 0;

  return (
    <section
      className={
        hideAnalysisHub
          ? "ppc-myweg-needs__evolution ppc-myweg-needs__evolution--compact"
          : "ppc-myweg-needs__evolution"
      }
      aria-label={texts.title}
    >
      {!hideAnalysisHub ? (
        <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
          {texts.intro}{" "}
          <HelpTooltip content={helpTooltips.mywegNeedsEvolution} trigger="icon" />
        </p>
      ) : null}

      {!hideAnalysisHub ? (
        <div
          className="ppc-myweg-needs__analysis-hub"
          role="group"
          aria-label={texts.analysisToggleAria}
        >
          <button
            type="button"
            className={
              activeAnalysis === "remessa"
                ? "ppc-myweg-needs__hub-card ppc-myweg-needs__hub-card--active"
                : "ppc-myweg-needs__hub-card"
            }
            aria-label={`${texts.analysisRemessa} — ${texts.analysisRemessaDesc}`}
            aria-pressed={activeAnalysis === "remessa"}
            onClick={() => onAnalysisChange?.("remessa")}
          >
            <span className="ppc-myweg-needs__hub-icon" aria-hidden="true">
              <CalendarClock size={22} strokeWidth={1.75} />
            </span>
            <span className="ppc-myweg-needs__hub-body">
              <span className="ppc-myweg-needs__hub-title">
                {texts.analysisRemessa}
                <HelpTooltip content={helpTooltips.mywegNeedsAnalysisRemessa} trigger="icon" />
              </span>
              <span className="ppc-myweg-needs__hub-desc">{texts.analysisRemessaDesc}</span>
            </span>
            <span className="ppc-myweg-needs__hub-go" aria-hidden="true">
              <ArrowRight size={18} strokeWidth={2} />
            </span>
          </button>

          <button
            type="button"
            className={
              activeAnalysis === "products"
                ? "ppc-myweg-needs__hub-card ppc-myweg-needs__hub-card--active"
                : "ppc-myweg-needs__hub-card"
            }
            aria-label={`${texts.analysisProducts} — ${texts.analysisProductsDesc}`}
            aria-pressed={activeAnalysis === "products"}
            onClick={() => onAnalysisChange?.("products")}
          >
            <span className="ppc-myweg-needs__hub-icon" aria-hidden="true">
              <Package size={22} strokeWidth={1.75} />
            </span>
            <span className="ppc-myweg-needs__hub-body">
              <span className="ppc-myweg-needs__hub-title">
                {texts.analysisProducts}
                <HelpTooltip content={helpTooltips.mywegNeedsAnalysisProducts} trigger="icon" />
              </span>
              <span className="ppc-myweg-needs__hub-desc">{texts.analysisProductsDesc}</span>
            </span>
            <span className="ppc-myweg-needs__hub-go" aria-hidden="true">
              <ArrowRight size={18} strokeWidth={2} />
            </span>
          </button>
        </div>
      ) : null}

      <section
        className={
          hideAnalysisHub
            ? "ppc-myweg-needs__filters-card ppc-myweg-needs__filters-card--toolbar"
            : "ppc-myweg-needs__filters-card"
        }
        aria-label={texts.filtersAria}
      >
        <div className="ppc-myweg-needs__filters-toolbar">
          <header className="ppc-myweg-needs__filters-header">
            <span className="ppc-myweg-needs__filters-icon" aria-hidden="true">
              <Filter size={16} strokeWidth={1.85} />
            </span>
            <h3 className="ppc-myweg-needs__filters-title">{texts.filtersTitle}</h3>
            {hideAnalysisHub ? (
              <HelpTooltip content={helpTooltips.mywegNeedsEvolution} trigger="icon" />
            ) : null}
          </header>

          <div className="ppc-myweg-needs__filters-toolbar-fields">
            <label className="ppc-myweg-needs__history">
              <span>{texts.fromLabel}</span>
              <select
                value={fromId}
                onChange={(event) => setFromId(event.target.value)}
                aria-label={texts.fromLabel}
              >
                <option value="">—</option>
                {historyItems.map((item) => (
                  <option key={`from-${item.id}`} value={item.id}>
                    {formatRemessaBr(item.collectionDate)} · {item.recordCount} regs
                  </option>
                ))}
              </select>
            </label>
            <label className="ppc-myweg-needs__history">
              <span>{texts.toLabel}</span>
              <select
                value={toId}
                onChange={(event) => setToId(event.target.value)}
                aria-label={texts.toLabel}
              >
                {historyItems.map((item) => (
                  <option key={`to-${item.id}`} value={item.id}>
                    {formatRemessaBr(item.collectionDate)} · {item.recordCount} regs
                  </option>
                ))}
              </select>
            </label>

            <label className="ppc-myweg-needs__search ppc-myweg-needs__filters-search">
              <span>
                {texts.productSearchLabel}{" "}
                <HelpTooltip content={texts.searchHint} trigger="icon" />
              </span>
              <span className="ppc-myweg-needs__filters-search-wrap">
                <Search
                  className="ppc-myweg-needs__filters-search-icon"
                  size={14}
                  strokeWidth={1.85}
                  aria-hidden
                />
                <input
                  type="search"
                  value={searchDraft}
                  placeholder={texts.searchPlaceholder}
                  onChange={(event) => setSearchDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      applySearch();
                    }
                  }}
                  aria-label={texts.searchLabel}
                />
              </span>
            </label>

            {activeAnalysis === "remessa" ? (
              <label className="ppc-myweg-needs__history ppc-myweg-needs__billing-toggle">
                <span>{texts.billingLabel}</span>
                <select
                  value={billingMode}
                  onChange={(event) =>
                    setBillingMode(event.target.value === "indicative" ? "indicative" : "none")
                  }
                >
                  <option value="none">{texts.billingNone}</option>
                  <option value="indicative">{texts.billingIndicative}</option>
                </select>
              </label>
            ) : null}
          </div>

          <div className="ppc-myweg-needs__filters-actions">
            <button type="button" className="ppc-btn ppc-btn--ghost" onClick={clearSearch}>
              <Eraser size={15} strokeWidth={1.75} aria-hidden />
              {texts.clearFilters}
            </button>
            <button type="button" className="ppc-btn ppc-btn--primary" onClick={applySearch}>
              <Search size={15} strokeWidth={1.75} aria-hidden />
              {texts.applyFilters}
            </button>
          </div>
        </div>
      </section>

      {activeAnalysis === "products" && fromId && toId && fromId !== toId ? (
        <MyWegProductConsolidationPanel fromId={fromId} toId={toId} search={search} />
      ) : null}
      {activeAnalysis === "products" && fromId && toId && fromId === toId ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {texts.chronoInvalid}
        </div>
      ) : null}

      {activeAnalysis === "remessa" && loading ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.loading}
        </p>
      ) : null}
      {activeAnalysis === "remessa" && status === 403 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {texts.forbidden}
        </div>
      ) : null}
      {activeAnalysis === "remessa" && status === 409 ? (
        <div className="ppc-state" role="status">
          {error || texts.insufficient}
        </div>
      ) : null}
      {activeAnalysis === "remessa" && status === 422 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || texts.chronoInvalid}
        </div>
      ) : null}
      {activeAnalysis === "remessa" &&
      error &&
      status !== 403 &&
      status !== 409 &&
      status !== 422 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {activeAnalysis === "remessa" && payload && !loading ? (
        <>
          <div className="ppc-myweg-needs__evolution-meta">
            <span className="ppc-myweg-needs__evolution-scope">
              {payload.scope.customerName} · {payload.scope.protheusCustomerCode}/
              {payload.scope.protheusCustomerStore}
            </span>
            <span className="ppc-myweg-needs__evolution-note" role="status">
              {texts.totalsHint(payload.totalCompared ?? 0, payload.totalChanges ?? 0)}
            </span>
          </div>

          <section className="ppc-myweg-needs__summary" aria-label={texts.summaryAria}>
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card ppc-myweg-needs__kpi-card--up"
              title={texts.kpi.increased}
              titleHint={helpTooltips.mywegNeedsKpiIncreased}
              icon={<TrendingUp size={20} strokeWidth={1.75} />}
              value={String(summary?.increased ?? 0)}
              comparisonTone="positive"
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card ppc-myweg-needs__kpi-card--down"
              title={texts.kpi.decreased}
              titleHint={helpTooltips.mywegNeedsKpiDecreased}
              icon={<TrendingDown size={20} strokeWidth={1.75} />}
              value={String(summary?.decreased ?? 0)}
              comparisonTone="negative"
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card ppc-myweg-needs__kpi-card--up"
              title={texts.kpi.appeared}
              titleHint={helpTooltips.mywegNeedsKpiAppeared}
              icon={<LogIn size={20} strokeWidth={1.75} />}
              value={String(summary?.appeared ?? 0)}
              comparisonTone="positive"
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card ppc-myweg-needs__kpi-card--down"
              title={texts.kpi.disappeared}
              titleHint={helpTooltips.mywegNeedsKpiDisappeared}
              icon={<LogOut size={20} strokeWidth={1.75} />}
              value={String(summary?.disappeared ?? 0)}
              comparisonTone="negative"
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card ppc-myweg-needs__kpi-card--horizon"
              title={texts.kpi.horizon}
              titleHint={helpTooltips.mywegNeedsKpiHorizon}
              icon={<CalendarClock size={20} strokeWidth={1.75} />}
              value={String(summary?.horizon_14d_changes ?? 0)}
            />
          </section>

          <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
            {texts.disclaimerCompact}
          </p>

          <MyWegProbableDateShiftsSection
            shifts={payload.observed.probableDateShifts}
            resetKey={`${payload.fromBatch.id}|${payload.toBatch.id}|${payload.observed.referenceDate}`}
          />

          {(payload.totalChanges ?? 0) === 0 && (payload.total ?? 0) === 0 && !search ? (
            <p role="status">{texts.noChanges}</p>
          ) : (
            <div data-testid="myweg-compare-table">
              <DataTableSection
                title={texts.tableTitle}
                rows={payload.items}
                columns={columns}
                rowKey={(row) => `${row.productKey}|${row.remessa}|${row.movement}`}
                emptyMessage={
                  search ? copy.tableSection.emptyMessage : texts.noChanges
                }
                hideSearch
                columnPreferencesKey="production-control:myweg-evolution:columns:v1"
                serverPagination={{
                  page: payload.page,
                  pageSize: payload.pageSize,
                  total: payload.total,
                  onPageChange: (nextPage) => setPage(nextPage),
                  onPageSizeChange: () => {
                    /* pageSize fixo 50 nesta etapa */
                  },
                }}
              />
            </div>
          )}

          <aside
            className={
              billingMode === "none"
                ? "ppc-myweg-needs__billing ppc-myweg-needs__billing--quiet"
                : "ppc-myweg-needs__billing"
            }
            aria-label={texts.billingAria}
          >
            {billingMode === "none" || billing?.status === "skipped" ? (
              <p className="ppc-myweg-needs__billing-quiet">{texts.billingSkipped}</p>
            ) : (
              <>
                <h3>{texts.billingTitle}</h3>
                {billing?.period ? (
                  <p>
                    <strong>{texts.periodLabel}:</strong> {billing.period.start} →{" "}
                    {billing.period.end}
                    {billing.periodTimezone ? ` (${billing.periodTimezone})` : ""}
                  </p>
                ) : null}
                {billing?.periodCriterion ? (
                  <p>
                    <strong>{texts.periodCriterionLabel}:</strong> {billing.periodCriterion}
                  </p>
                ) : null}
                {billing?.cutoffUncertainty ? (
                  <p>
                    <strong>{texts.cutoffLabel}:</strong> {billing.cutoffUncertainty}
                  </p>
                ) : null}
                <p>{billing?.disclaimer || texts.billingSkipped}</p>
                {billing?.status === "unavailable" ? (
                  <p role="status">{texts.billingUnavailable}</p>
                ) : null}
                {billing?.status === "empty" ? (
                  <p role="status">{texts.billingEmpty}</p>
                ) : null}
                {billing?.status === "incompatible_units" ? (
                  <p role="status">{texts.billingIncompatible}</p>
                ) : null}
                {billing?.status === "partial" ? (
                  <p role="status">{texts.billingPartial}</p>
                ) : null}
                {showBillingTable ? (
                  <DataTableSection
                    title={texts.indicativeTableTitle}
                    rows={indicativeRows}
                    columns={indicativeColumns}
                    rowKey={(row) => row.productCode}
                    emptyMessage={texts.billingEmpty}
                    hideSearch
                    columnPreferencesKey="production-control:myweg-evolution-billing:columns:v1"
                  />
                ) : null}
              </>
            )}
          </aside>
        </>
      ) : null}
    </section>
  );
}
