import {
  createDashboardKpiCard,
  HelpTooltip,
} from "@delpi/plugin-ui/index";
import {
  ArrowLeftRight,
  CalendarDays,
  Check,
  FileText,
  Layers,
  RefreshCw,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchMyWegInvoiceObservation,
  fetchMyWegInvoiceObservationItems,
  fetchMyWegNeedBatchesCompareProducts,
} from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type {
  MyWegCompareProductsPayload,
  MyWegInvoiceMode,
  MyWegInvoiceObservationItem,
  MyWegProductConsolidation,
} from "../types";
import { formatDecimalString } from "../utils/formatDecimalString";
import { formatPercentDisplay } from "../utils/formatPercentDisplay";
import {
  canShowPostedAsFact,
  completeCoverageDetailLabel,
  coverageStatusLabel,
  formatNullableDecimal,
  invoiceMatchStatusLabel,
  isCoverageComplete,
  lastCoveredDocumentDate,
  nullableDeltaToneClass,
} from "../utils/mywegInvoiceReconciliationUi";
import {
  deltaToneClass,
  situationBadgeClass,
} from "../utils/mywegSemanticTone";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { HostContainedWideDialog } from "./PpcConfirmModal";

type Props = {
  fromId: string;
  toId: string;
  search: string;
};

const texts = copy.mywegNeeds.evolution.products;
const PAGE_SIZE = 50;
const PENDING_POLL_MS = 60_000;
const MAX_ITEM_PAGES = 10;

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

function formatRemessaBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
}

function situationLabel(situation: string): string {
  switch (situation) {
    case "increased":
      return texts.situation.increased;
    case "decreased":
      return texts.situation.decreased;
    case "unchanged":
      return texts.situation.unchanged;
    case "stable_with_date_changes":
      return texts.situation.stableWithDateChanges;
    case "appeared":
      return texts.situation.appeared;
    case "disappeared":
      return texts.situation.disappeared;
    default:
      return situation;
  }
}

function movementLabel(movement: string): string {
  const base = copy.mywegNeeds.evolution.movement;
  switch (movement) {
    case "increased":
      return base.increased;
    case "decreased":
      return base.decreased;
    case "appeared":
      return base.appeared;
    case "disappeared":
      return base.disappeared;
    case "unchanged":
      return base.unchanged;
    default:
      return movement;
  }
}

function productLabel(row: MyWegProductConsolidation): string {
  if (row.identityConfirmed && row.verifiedProductCode) {
    return row.verifiedProductCode;
  }
  return (
    row.verifiedProductCode ||
    row.materialWegTratado ||
    row.codigoReferenciaWeg ||
    row.productKey ||
    "—"
  );
}

type FiscalLine = MyWegInvoiceObservationItem & {
  documentDate: string;
  observationId: string;
};

async function loadExactMaterialFiscalLines(params: {
  observationIds: string[];
  materials: string[];
  signal: AbortSignal;
}): Promise<{ lines: FiscalLine[]; incomplete: boolean }> {
  const materialSet = new Set(params.materials.map((m) => m.trim()).filter(Boolean));
  if (materialSet.size === 0 || params.observationIds.length === 0) {
    return { lines: [], incomplete: false };
  }

  const lines: FiscalLine[] = [];
  let incomplete = false;

  for (const observationId of params.observationIds) {
    if (params.signal.aborted) break;
    let documentDate = "";
    try {
      const observation = await fetchMyWegInvoiceObservation({
        observationId,
        signal: params.signal,
      });
      documentDate = observation.documentDate;
    } catch {
      incomplete = true;
      continue;
    }

    for (const material of materialSet) {
      let page = 1;
      let total = Infinity;
      while (page <= MAX_ITEM_PAGES && (page - 1) * 50 < total) {
        if (params.signal.aborted) break;
        try {
          const payload = await fetchMyWegInvoiceObservationItems({
            observationId,
            search: material,
            page,
            pageSize: 50,
            signal: params.signal,
          });
          total = payload.total;
          for (const item of payload.items) {
            if (item.materialWeg.trim() !== material) continue;
            lines.push({
              ...item,
              documentDate: documentDate || payload.documentDate,
              observationId,
            });
          }
          if (payload.items.length === 0) break;
          page += 1;
          if (page > MAX_ITEM_PAGES && (page - 1) * 50 < total) {
            incomplete = true;
          }
        } catch {
          incomplete = true;
          break;
        }
      }
    }
  }

  const seen = new Set<string>();
  const deduped: FiscalLine[] = [];
  for (const line of lines) {
    const key = [
      line.observationId,
      line.invoiceNumber,
      line.invoiceSeries,
      line.materialWeg,
      line.quantityUn ?? line.quantityOriginal,
      line.departureDate,
      line.sourceLineNo,
    ].join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(line);
  }
  return { lines: deduped, incomplete };
}

function ProductDetail({
  row,
  fromLabel,
  toLabel,
  invoiceMode,
  coverageStatus,
}: {
  row: MyWegProductConsolidation;
  fromLabel: string;
  toLabel: string;
  invoiceMode: MyWegInvoiceMode;
  coverageStatus?: string;
}) {
  const [fiscalLines, setFiscalLines] = useState<FiscalLine[]>([]);
  const [fiscalLoading, setFiscalLoading] = useState(false);
  const [fiscalIncomplete, setFiscalIncomplete] = useState(false);
  const [fiscalError, setFiscalError] = useState<string | null>(null);

  const materials = useMemo(
    () =>
      (row.portalInvoiceMaterials ?? [])
        .map((item) => item.materialWeg?.trim())
        .filter((value): value is string => Boolean(value)),
    [row.portalInvoiceMaterials],
  );
  const sources = useMemo(
    () => [...(row.portalInvoiceSources ?? [])],
    [row.portalInvoiceSources],
  );
  const materialsKey = materials.join("|");
  const sourcesKey = sources.join("|");
  const canLoadFiscal =
    invoiceMode === "portal" &&
    sources.length > 0 &&
    materials.length > 0 &&
    row.invoiceMatchStatus !== "attributed_elsewhere";

  useEffect(() => {
    if (!canLoadFiscal) {
      setFiscalLines([]);
      setFiscalIncomplete(false);
      setFiscalError(null);
      return;
    }
    const controller = new AbortController();
    setFiscalLoading(true);
    setFiscalError(null);
    void loadExactMaterialFiscalLines({
      observationIds: sourcesKey ? sourcesKey.split("|") : [],
      materials: materialsKey ? materialsKey.split("|") : [],
      signal: controller.signal,
    })
      .then((result) => {
        if (controller.signal.aborted) return;
        setFiscalLines(result.lines);
        setFiscalIncomplete(result.incomplete);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setFiscalLines([]);
        setFiscalError(
          err instanceof Error ? err.message : texts.fiscalLinesGap,
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setFiscalLoading(false);
      });
    return () => controller.abort();
  }, [canLoadFiscal, materialsKey, sourcesKey]);

  const observed =
    row.observedDeltaUn ?? row.deltaQuantityUn;
  const showPosted = canShowPostedAsFact(coverageStatus, row.postedQuantityUn);

  return (
    <div className="ppc-myweg-needs__product-detail">
      <div className="ppc-myweg-needs__product-detail-meta">
        <span>
          <strong>{texts.detailPair}:</strong> {fromLabel} → {toLabel}
        </span>
        <span>
          <strong>{texts.detailTotals}:</strong>{" "}
          {formatDecimalString(row.previousQuantityUn)} →{" "}
          {formatDecimalString(row.currentQuantityUn)} UN (
          <span className={deltaToneClass(row.situation)}>
            {formatDecimalString(row.deltaQuantityUn)}
          </span>
          )
        </span>
      </div>
      {!row.identityConfirmed ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.identityUnconfirmed}
        </p>
      ) : null}
      {row.portalInvoiceOrphan ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.fiscalOrphanBadge}
        </p>
      ) : null}

      {invoiceMode === "portal" ? (
        <section
          className="ppc-myweg-needs__fiscal-detail"
          aria-label={texts.fiscalSectionTitle}
        >
          <h4>
            {texts.fiscalSectionTitle}
            <HelpTooltip
              content={helpTooltips.mywegNeedsInvoiceReconciliation}
              trigger="icon"
            />
          </h4>
          <ul className="ppc-myweg-needs__fiscal-summary">
            <li>
              <strong>{texts.columns.observed}:</strong>{" "}
              <span className={nullableDeltaToneClass(observed)}>
                {formatNullableDecimal(observed, texts.unavailableValue)} UN
              </span>
            </li>
            <li>
              <strong>{texts.columns.posted}:</strong>{" "}
              {showPosted
                ? `${formatDecimalString(row.postedQuantityUn)} UN`
                : texts.unavailableValue}
            </li>
            <li>
              <strong>{texts.columns.adjusted}:</strong>{" "}
              <span className={nullableDeltaToneClass(row.adjustedPlanningDeltaUn)}>
                {formatNullableDecimal(
                  row.adjustedPlanningDeltaUn,
                  texts.unavailableValue,
                )}
                {row.adjustedPlanningDeltaUn != null ? " UN" : ""}
              </span>
            </li>
            <li>
              <strong>{texts.columns.matchStatus}:</strong>{" "}
              {invoiceMatchStatusLabel(row.invoiceMatchStatus)}
            </li>
          </ul>

          {row.invoiceMatchStatus === "attributed_elsewhere" ? (
            <p className="ppc-myweg-needs__evolution-note" role="status">
              {texts.fiscalAttributedElsewhere}
            </p>
          ) : null}

          {materials.length > 0 ? (
            <div className="ppc-myweg-needs__fiscal-materials">
              <h5>{texts.fiscalMaterialsTitle}</h5>
              <ul>
                {(row.portalInvoiceMaterials ?? []).map((material) => (
                  <li key={`${row.productKey}|${material.materialWeg}`}>
                    {material.materialWeg}
                    {material.note ? ` — ${material.note}` : null}
                    {material.postedQuantityUn != null && showPosted
                      ? ` · NF ${formatDecimalString(material.postedQuantityUn)} UN`
                      : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {sources.length > 0 ? (
            <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
              <strong>{texts.fiscalSourcesTitle}:</strong> {sources.length} referência
              {sources.length === 1 ? "" : "s"}
            </p>
          ) : null}

          {canLoadFiscal ? (
            <div className="ppc-myweg-needs__shifts-table-wrap">
              <table className="ppc-myweg-needs__shifts-table">
                <caption className="ppc-myweg-needs__product-detail-caption">
                  {texts.fiscalLinesTitle}
                </caption>
                <thead>
                  <tr>
                    <th scope="col">{texts.fiscalColumns.invoice}</th>
                    <th scope="col">{texts.fiscalColumns.series}</th>
                    <th scope="col">{texts.fiscalColumns.material}</th>
                    <th scope="col">{texts.fiscalColumns.quantity}</th>
                    <th scope="col">{texts.fiscalColumns.documentDate}</th>
                    <th scope="col">{texts.fiscalColumns.departureDate}</th>
                  </tr>
                </thead>
                <tbody>
                  {fiscalLoading ? (
                    <tr>
                      <td colSpan={6}>{texts.fiscalLinesLoading}</td>
                    </tr>
                  ) : fiscalError ? (
                    <tr>
                      <td colSpan={6}>{fiscalError}</td>
                    </tr>
                  ) : fiscalLines.length === 0 ? (
                    <tr>
                      <td colSpan={6}>{texts.fiscalLinesEmpty}</td>
                    </tr>
                  ) : (
                    fiscalLines.map((line) => (
                      <tr
                        key={`${line.observationId}|${line.id}|${line.sourceLineNo}`}
                      >
                        <td>{line.invoiceNumber}</td>
                        <td>{line.invoiceSeries}</td>
                        <td>{line.materialWeg}</td>
                        <td>
                          {line.quantityUn != null
                            ? formatDecimalString(line.quantityUn)
                            : texts.unavailableValue}
                        </td>
                        <td>{formatRemessaBr(line.documentDate)}</td>
                        <td>{formatRemessaBr(line.departureDate)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              {fiscalIncomplete ? (
                <p className="ppc-myweg-needs__evolution-note" role="status">
                  {texts.fiscalLinesGap}
                </p>
              ) : null}
            </div>
          ) : invoiceMode === "portal" ? (
            <p className="ppc-myweg-needs__evolution-note" role="status">
              {texts.fiscalLinesGap}
            </p>
          ) : null}
        </section>
      ) : null}

      <div className="ppc-myweg-needs__shifts-table-wrap">
        <table className="ppc-myweg-needs__shifts-table">
          <caption className="ppc-myweg-needs__product-detail-caption">
            {texts.remessaTableTitle}
          </caption>
          <thead>
            <tr>
              <th scope="col">{texts.remessaColumns.remessa}</th>
              <th scope="col">{texts.remessaColumns.previous}</th>
              <th scope="col">{texts.remessaColumns.current}</th>
              <th scope="col">{texts.remessaColumns.delta}</th>
              <th scope="col">{texts.remessaColumns.situation}</th>
            </tr>
          </thead>
          <tbody>
            {row.remessas.map((item) => (
              <tr key={`${row.productKey}|${item.remessa}|${item.movement}`}>
                <td>{formatRemessaBr(item.remessa)}</td>
                <td>{formatDecimalString(item.previousQuantityUn)}</td>
                <td>{formatDecimalString(item.currentQuantityUn)}</td>
                <td>
                  <span className={deltaToneClass(item.movement)}>
                    {formatDecimalString(item.deltaQuantityUn)}
                  </span>
                </td>
                <td>
                  <span className={situationBadgeClass(item.movement)}>
                    {movementLabel(item.movement)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {row.probableDateShifts.length > 0 ? (
        <div className="ppc-myweg-needs__product-shifts">
          <h4>{texts.relatedShiftsTitle}</h4>
          <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
            {texts.relatedShiftsNote}
          </p>
          <ul>
            {row.probableDateShifts.map((shift, index) => (
              <li
                key={`${shift.productKey}|${shift.fromRemessa}|${shift.toRemessa}|${index}`}
              >
                {shift.kind === "possible_advancement"
                  ? texts.shiftAdvancement
                  : shift.kind === "possible_postponement"
                    ? texts.shiftPostponement
                    : texts.shiftOther}
                : {formatDecimalString(shift.quantityUn)} UN ·{" "}
                {formatRemessaBr(shift.fromRemessa)} →{" "}
                {formatRemessaBr(shift.toRemessa)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function MyWegProductConsolidationPanel({ fromId, toId, search }: Props) {
  const [page, setPage] = useState(1);
  const [invoiceMode, setInvoiceMode] = useState<MyWegInvoiceMode>("none");
  const [refreshToken, setRefreshToken] = useState(0);
  const [payload, setPayload] = useState<MyWegCompareProductsPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const requestSeq = useRef(0);

  const openDetail = (productKey: string) => {
    setSelectedKey(productKey);
  };

  const closeDetail = () => {
    setSelectedKey(null);
  };

  useEffect(() => {
    setPage(1);
    setSelectedKey(null);
  }, [fromId, toId, search, invoiceMode]);

  useEffect(() => {
    if (!fromId || !toId || fromId === toId) {
      setPayload(null);
      return;
    }
    const controller = new AbortController();
    const seq = ++requestSeq.current;
    setLoading(true);
    setError(null);
    setStatus(null);
    void fetchMyWegNeedBatchesCompareProducts({
      fromBatchId: fromId,
      toBatchId: toId,
      search,
      page,
      pageSize: PAGE_SIZE,
      changesOnly: true,
      invoiceMode,
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setPayload(data);
      })
      .catch((err) => {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setPayload(null);
        setStatus(httpErrorStatus(err));
        setError(err instanceof Error ? err.message : texts.loadError);
      })
      .finally(() => {
        if (!controller.signal.aborted && seq === requestSeq.current) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [fromId, toId, search, page, invoiceMode, refreshToken]);

  const coverageStatus = payload?.portalInvoices?.status;
  const pendingIngestion =
    invoiceMode === "portal" && coverageStatus === "pending_invoice_ingestion";

  useEffect(() => {
    if (!pendingIngestion) return;
    const timer = window.setInterval(() => {
      setRefreshToken((value) => value + 1);
    }, PENDING_POLL_MS);
    return () => window.clearInterval(timer);
  }, [pendingIngestion]);

  const columns = useMemo<DataTableColumn<MyWegProductConsolidation>[]>(() => {
    const base: DataTableColumn<MyWegProductConsolidation>[] = [
      {
        key: "product",
        header: texts.columns.product,
        render: (row) => (
          <span>
            <span className="ppc-myweg-needs__shifts-product">{productLabel(row)}</span>
            {!row.identityConfirmed ? (
              <span className="ppc-myweg-needs__shifts-identity">
                {texts.identityUnconfirmed}
              </span>
            ) : null}
            {row.portalInvoiceOrphan ? (
              <span className="ppc-myweg-needs__shifts-identity">
                {texts.fiscalOrphanBadge}
              </span>
            ) : null}
          </span>
        ),
      },
      {
        key: "previous",
        header: texts.columns.previous,
        headerHint: "Necessidade total na coleta anterior (UN)",
        align: "right",
        render: (row) => formatDecimalString(row.previousQuantityUn),
      },
      {
        key: "current",
        header: texts.columns.current,
        headerHint: "Necessidade total na coleta atual (UN)",
        align: "right",
        render: (row) => formatDecimalString(row.currentQuantityUn),
      },
    ];

    if (invoiceMode === "portal") {
      base.push(
        {
          key: "observed",
          header: texts.columns.observed,
          headerHint: helpTooltips.mywegNeedsObservedDelta,
          align: "right",
          render: (row) => {
            const value = row.observedDeltaUn ?? row.deltaQuantityUn;
            return (
              <span className={nullableDeltaToneClass(value)}>
                {formatNullableDecimal(value, texts.unavailableValue)}
              </span>
            );
          },
        },
        {
          key: "posted",
          header: texts.columns.posted,
          headerHint: helpTooltips.mywegNeedsPostedNf,
          align: "right",
          render: (row) =>
            canShowPostedAsFact(coverageStatus, row.postedQuantityUn)
              ? formatDecimalString(row.postedQuantityUn)
              : texts.unavailableValue,
        },
        {
          key: "adjusted",
          header: texts.columns.adjusted,
          headerHint: helpTooltips.mywegNeedsAdjustedDelta,
          align: "right",
          render: (row) => (
            <span className={nullableDeltaToneClass(row.adjustedPlanningDeltaUn)}>
              {formatNullableDecimal(
                row.adjustedPlanningDeltaUn,
                texts.unavailableValue,
              )}
            </span>
          ),
        },
        {
          key: "matchStatus",
          header: texts.columns.matchStatus,
          headerHint: helpTooltips.mywegNeedsInvoiceReconciliation,
          render: (row) => invoiceMatchStatusLabel(row.invoiceMatchStatus),
        },
        {
          key: "delta",
          header: texts.columns.delta,
          headerHint: "Diferença líquida = atual − anterior (UN)",
          align: "right",
          render: (row) => (
            <span className={deltaToneClass(row.situation)}>
              {formatDecimalString(row.deltaQuantityUn)}
            </span>
          ),
        },
        {
          key: "percent",
          header: texts.columns.percent,
          headerHint: "Variação percentual da necessidade total",
          align: "right",
          render: (row) => (
            <span className={deltaToneClass(row.situation)}>
              {formatPercentDisplay(row.percentChange)}
            </span>
          ),
        },
        {
          key: "situation",
          header: texts.columns.situation,
          headerHint: helpTooltips.mywegNeedsProductAnalysis,
          render: (row) => (
            <span className={situationBadgeClass(row.situation)}>
              {situationLabel(row.situation)}
            </span>
          ),
        },
      );
    } else {
      base.push(
        {
          key: "delta",
          header: texts.columns.delta,
          headerHint: "Diferença líquida = atual − anterior (UN)",
          align: "right",
          render: (row) => (
            <span className={deltaToneClass(row.situation)}>
              {formatDecimalString(row.deltaQuantityUn)}
            </span>
          ),
        },
        {
          key: "percent",
          header: texts.columns.percent,
          headerHint: "Variação percentual da necessidade total",
          align: "right",
          render: (row) => (
            <span className={deltaToneClass(row.situation)}>
              {formatPercentDisplay(row.percentChange)}
            </span>
          ),
        },
        {
          key: "situation",
          header: texts.columns.situation,
          headerHint: helpTooltips.mywegNeedsProductAnalysis,
          render: (row) => (
            <span className={situationBadgeClass(row.situation)}>
              {situationLabel(row.situation)}
            </span>
          ),
        },
      );
    }

    base.push({
      key: "details",
      header: texts.columns.details,
      interactive: true,
      rowClick: "stop",
      render: (row) => (
        <button
          type="button"
          className="ppc-btn ppc-btn--secondary ppc-myweg-needs__details-btn"
          aria-haspopup="dialog"
          aria-expanded={selectedKey === row.productKey}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            openDetail(row.productKey);
          }}
        >
          {texts.showDetails}
        </button>
      ),
    });

    return base;
  }, [coverageStatus, invoiceMode, selectedKey]);

  if (!fromId || !toId || fromId === toId) {
    return null;
  }

  const selected =
    payload?.items.find((row) => row.productKey === selectedKey) ?? null;
  const fromLabel = formatRemessaBr(payload?.fromBatch.collectionDate);
  const toLabel = formatRemessaBr(payload?.toBatch.collectionDate);
  const netDelta = payload
    ? formatDecimalString(payload.totals.deltaQuantityUn)
    : null;
  const netToneClass = nullableDeltaToneClass(payload?.totals.deltaQuantityUn);
  const detailOpen = Boolean(selected);
  const portal = payload?.portalInvoices;
  const coveredCount =
    portal?.coveredDayCount ?? portal?.coveredDates?.length ?? null;
  const missingCount =
    portal?.missingDayCount ?? portal?.missingDates?.length ?? null;
  const lastFiscal = lastCoveredDocumentDate({
    coveredDates: portal?.coveredDates,
    canonicalObservations: portal?.canonicalObservations,
  });
  const coverageLabel =
    isCoverageComplete(coverageStatus) &&
    canShowPostedAsFact(coverageStatus, payload?.totals.postedQuantityUn)
      ? completeCoverageDetailLabel(payload?.totals.postedQuantityUn) === "Com NF"
        ? texts.coverageCompleteWithNf
        : texts.coverageCompleteWithoutNf
      : coverageStatusLabel(coverageStatus);
  const periodFrom = portal?.period?.fromDocumentDate ?? portal?.period?.start;
  const periodToExclusive =
    portal?.period?.toDocumentDateExclusive ?? portal?.period?.end;

  return (
    <section className="ppc-myweg-needs__products" aria-label={texts.title}>
      <header className="ppc-myweg-needs__products-header">
        <div className="ppc-myweg-needs__products-summary">
          <div className="ppc-myweg-needs__products-summary-copy">
            <h3 className="ppc-myweg-needs__shifts-title">
              <Layers size={18} strokeWidth={1.85} aria-hidden />
              {texts.title}
              <HelpTooltip
                content={
                  invoiceMode === "portal"
                    ? helpTooltips.mywegNeedsInvoiceReconciliation
                    : helpTooltips.mywegNeedsProductAnalysis
                }
                trigger="icon"
              />
            </h3>
            <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
              {invoiceMode === "portal" ? texts.invoiceModeIntro : texts.intro}
            </p>
          </div>

          {payload ? (
            <div className="ppc-myweg-needs__products-stats" role="status">
              <div className="ppc-myweg-needs__stat-card ppc-myweg-needs__stat-card--changed">
                <ArrowLeftRight size={16} strokeWidth={1.85} aria-hidden />
                <strong>{payload.totalProductsChanged.toLocaleString("pt-BR")}</strong>
                <span>{texts.statsChangedLabel}</span>
              </div>
              <div className="ppc-myweg-needs__stat-card ppc-myweg-needs__stat-card--compared">
                <Check size={16} strokeWidth={2} aria-hidden />
                <strong>{payload.totalProductsCompared.toLocaleString("pt-BR")}</strong>
                <span>{texts.statsComparedLabel}</span>
              </div>
              <div
                className={`ppc-myweg-needs__stat-card ppc-myweg-needs__stat-card--delta ${netToneClass}`}
              >
                <Layers size={16} strokeWidth={1.85} aria-hidden />
                <strong>{netDelta ?? "—"} UN</strong>
                <span>{texts.statsDeltaLabel}</span>
              </div>
            </div>
          ) : null}
        </div>

        <div
          className="ppc-myweg-needs__invoice-mode"
          role="group"
          aria-label={texts.invoiceModeToggleAria}
        >
          <button
            type="button"
            className={
              invoiceMode === "none"
                ? "ppc-myweg-needs__invoice-mode-btn ppc-myweg-needs__invoice-mode-btn--active"
                : "ppc-myweg-needs__invoice-mode-btn"
            }
            aria-pressed={invoiceMode === "none"}
            onClick={() => setInvoiceMode("none")}
          >
            {texts.invoiceModeNeeds}
          </button>
          <button
            type="button"
            className={
              invoiceMode === "portal"
                ? "ppc-myweg-needs__invoice-mode-btn ppc-myweg-needs__invoice-mode-btn--active"
                : "ppc-myweg-needs__invoice-mode-btn"
            }
            aria-pressed={invoiceMode === "portal"}
            onClick={() => setInvoiceMode("portal")}
          >
            {texts.invoiceModePortal}
          </button>
          {invoiceMode === "portal" ? (
            <button
              type="button"
              className="ppc-btn ppc-btn--secondary ppc-myweg-needs__refresh-btn"
              onClick={() => setRefreshToken((value) => value + 1)}
              disabled={loading}
            >
              <RefreshCw size={14} aria-hidden />
              {loading ? texts.refreshing : texts.refreshReconciliation}
            </button>
          ) : null}
        </div>
      </header>

      {status === 403 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {texts.forbidden}
        </div>
      ) : null}
      {error && status !== 403 ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error}
        </div>
      ) : null}
      {loading && !payload ? <p role="status">{texts.loading}</p> : null}

      {invoiceMode === "portal" && payload && portal ? (
        <div
          className="ppc-myweg-needs__portal-kpis"
          aria-label="Resumo da conciliação fiscal"
        >
          <div className="ppc-kpi-grid ppc-myweg-needs__portal-kpi-grid">
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiPosted}
              titleHint={helpTooltips.mywegNeedsPostedNf}
              icon={<FileText size={20} strokeWidth={1.75} />}
              value={
                canShowPostedAsFact(coverageStatus, payload.totals.postedQuantityUn)
                  ? `${formatDecimalString(payload.totals.postedQuantityUn)} UN`
                  : texts.unavailableValue
              }
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiObserved}
              titleHint={helpTooltips.mywegNeedsObservedDelta}
              icon={<TrendingDown size={20} strokeWidth={1.75} />}
              value={(() => {
                const observed =
                  payload.totals.observedDeltaUn ?? payload.totals.deltaQuantityUn;
                if (observed == null || String(observed).trim() === "") {
                  return texts.unavailableValue;
                }
                return `${formatDecimalString(observed)} UN`;
              })()}
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiAdjusted}
              titleHint={helpTooltips.mywegNeedsAdjustedDelta}
              icon={<TrendingUp size={20} strokeWidth={1.75} />}
              value={
                payload.totals.adjustedPlanningDeltaUn == null ||
                String(payload.totals.adjustedPlanningDeltaUn).trim() === ""
                  ? texts.unavailableValue
                  : `${formatDecimalString(payload.totals.adjustedPlanningDeltaUn)} UN`
              }
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiCoverage}
              titleHint={helpTooltips.mywegNeedsFiscalCoverage}
              icon={<ShieldAlert size={20} strokeWidth={1.75} />}
              value={coverageLabel}
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiCoveredDays}
              titleHint={helpTooltips.mywegNeedsFiscalCoverage}
              icon={<CalendarDays size={20} strokeWidth={1.75} />}
              value={coveredCount == null ? "—" : String(coveredCount)}
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiMissingDays}
              titleHint={helpTooltips.mywegNeedsFiscalCoverage}
              icon={<CalendarDays size={20} strokeWidth={1.75} />}
              value={missingCount == null ? "—" : String(missingCount)}
            />
            <KpiCard
              className="ppc-board-card ppc-myweg-needs__kpi-card"
              title={texts.kpiLastFiscalDate}
              titleHint={helpTooltips.mywegNeedsFiscalCoverage}
              icon={<CalendarDays size={20} strokeWidth={1.75} />}
              value={formatRemessaBr(lastFiscal)}
            />
          </div>
          {periodFrom || periodToExclusive ? (
            <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
              {texts.fiscalPeriodLabel}: {formatRemessaBr(periodFrom)} até antes de{" "}
              {formatRemessaBr(periodToExclusive)}
            </p>
          ) : null}
          {portal.disclaimer ? (
            <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
              {portal.disclaimer}
            </p>
          ) : null}
        </div>
      ) : null}

      {payload && status !== 403 ? (
        <DataTableSection
          title={
            invoiceMode === "portal"
              ? `${texts.tableTitle} · ${texts.invoiceModePortal}`
              : texts.tableTitle
          }
          rows={payload.items}
          columns={columns}
          rowKey={(row) => row.productKey}
          emptyMessage={search ? copy.tableSection.emptyMessage : texts.empty}
          hideSearch
          interactive
          columnPreferencesKey="production-control:myweg-products:columns:v1"
          onRowClick={(row) => openDetail(row.productKey)}
          getRowClassName={(row) =>
            row.productKey === selectedKey
              ? "ppc-myweg-needs__product-row--selected"
              : undefined
          }
          serverPagination={{
            page: payload.page,
            pageSize: payload.pageSize,
            total: payload.total,
            onPageChange: (nextPage) => {
              setSelectedKey(null);
              setPage(nextPage);
            },
            onPageSizeChange: () => {
              /* pageSize fixo 50 nesta etapa */
            },
          }}
        />
      ) : null}

      <HostContainedWideDialog
        open={detailOpen}
        title={selected ? texts.detailHeading(productLabel(selected)) : texts.title}
        onClose={closeDetail}
        closeAriaLabel={texts.detailCloseAria}
      >
        {selected ? (
          <ProductDetail
            row={selected}
            fromLabel={fromLabel}
            toLabel={toLabel}
            invoiceMode={invoiceMode}
            coverageStatus={coverageStatus}
          />
        ) : null}
      </HostContainedWideDialog>
    </section>
  );
}
