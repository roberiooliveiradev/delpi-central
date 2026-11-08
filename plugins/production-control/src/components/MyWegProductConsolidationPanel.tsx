import { HelpTooltip } from "@delpi/plugin-ui/index";
import { ArrowLeftRight, Check, Layers, RefreshCw } from "lucide-react";
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
  formatNullableDecimal,
  managerialBadgeClass,
  managerialStatusHint,
  managerialStatusLabel,
  nullableDeltaToneClass,
  observedDeltaToneClass,
  remessaContextLabel,
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

function formatRemessaBr(value: string | null | undefined): string {
  const text = (value ?? "").trim();
  if (!text) return "—";
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const [y, m, d] = text.slice(0, 10).split("-");
    return `${d}/${m}/${y}`;
  }
  return text;
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
  coverageStatus,
}: {
  row: MyWegProductConsolidation;
  fromLabel: string;
  toLabel: string;
  coverageStatus?: string;
}) {
  const [fiscalLines, setFiscalLines] = useState<FiscalLine[]>([]);
  const [fiscalLoading, setFiscalLoading] = useState(false);
  const [fiscalIncomplete, setFiscalIncomplete] = useState(false);
  const [fiscalError, setFiscalError] = useState<string | null>(null);
  const [showAudit, setShowAudit] = useState(false);

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

  const showPosted = canShowPostedAsFact(coverageStatus, row.postedQuantityUn);
  const managerial = row.managerialStatus;
  const residual = row.residualUnexplainedUn;
  const fiscalExcess = row.fiscalExcessUn;
  const showResidual =
    residual != null &&
    String(residual).trim() !== "" &&
    String(residual).trim() !== "0" &&
    String(residual).trim() !== "0.0" &&
    String(residual).trim() !== "0.00";
  const showFiscalExcess =
    managerial === "invoicing_with_difference" &&
    fiscalExcess != null &&
    String(fiscalExcess).trim() !== "";
  const hint = managerialStatusHint(managerial);

  return (
    <div className="ppc-myweg-needs__product-detail">
      <header className="ppc-myweg-needs__product-detail-header">
        <div>
          <p className="ppc-myweg-needs__product-detail-subtitle">
            {fromLabel} → {toLabel}
          </p>
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
        </div>
        <span className={managerialBadgeClass(managerial)} title={hint || undefined}>
          {managerialStatusLabel(managerial)}
          {hint ? (
            <span className="ppc-myweg-needs__mgr-badge-hint">{hint}</span>
          ) : null}
        </span>
      </header>

      <div
        className="ppc-myweg-needs__product-summary-kpis"
        aria-label={texts.detailSummaryAria}
      >
        <div className="ppc-myweg-needs__product-summary-kpi">
          <span>{texts.kpiPreviousNeed}</span>
          <strong>{formatDecimalString(row.previousQuantityUn)} UN</strong>
        </div>
        <div className="ppc-myweg-needs__product-summary-kpi">
          <span>{texts.kpiCurrentNeed}</span>
          <strong>{formatDecimalString(row.currentQuantityUn)} UN</strong>
        </div>
        <div className="ppc-myweg-needs__product-summary-kpi">
          <span>{texts.columns.posted}</span>
          <strong>
            {showPosted
              ? `${formatDecimalString(row.postedQuantityUn)} UN`
              : texts.unavailableValue}
          </strong>
        </div>
        {showFiscalExcess ? (
          <div className="ppc-myweg-needs__product-summary-kpi ppc-myweg-needs__product-summary-kpi--excess">
            <span>{texts.kpiFiscalExcess}</span>
            <strong>+{formatDecimalString(fiscalExcess)} UN</strong>
          </div>
        ) : showResidual || managerial === "partial_invoicing" ? (
          <div className="ppc-myweg-needs__product-summary-kpi ppc-myweg-needs__product-summary-kpi--residual">
            <span>{texts.kpiResidualUnexplained}</span>
            <strong>
              {residual != null && String(residual).trim() !== ""
                ? `${formatDecimalString(residual)} UN`
                : texts.unavailableValue}
            </strong>
          </div>
        ) : managerial === "invoiced" ? (
          <div className="ppc-myweg-needs__product-summary-kpi">
            <span>{texts.kpiResidualUnexplained}</span>
            <strong>0 UN</strong>
          </div>
        ) : null}
      </div>

      {row.managerialExplanation ? (
        <p
          className={
            managerial === "invoicing_with_difference"
              ? "ppc-myweg-needs__product-explanation ppc-myweg-needs__product-explanation--difference"
              : "ppc-myweg-needs__product-explanation"
          }
          role="status"
        >
          {row.managerialExplanation}
        </p>
      ) : null}

      {row.invoiceMatchStatus === "attributed_elsewhere" ? (
        <p className="ppc-myweg-needs__evolution-note" role="status">
          {texts.fiscalAttributedElsewhere}
        </p>
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
            {row.remessas.map((item) => {
              const remessaCtx = remessaContextLabel(item.managerialRemessaContext);
              const unchanged =
                item.movement === "unchanged" ||
                String(item.deltaQuantityUn).trim() === "0" ||
                String(item.deltaQuantityUn).trim() === "0.0" ||
                String(item.deltaQuantityUn).trim() === "0.00";
              const deltaClass = remessaCtx
                ? "ppc-myweg-needs__delta ppc-myweg-needs__delta--invoiced"
                : deltaToneClass(item.movement);
              return (
                <tr
                  key={`${row.productKey}|${item.remessa}|${item.movement}`}
                  className={
                    unchanged
                      ? "ppc-myweg-needs__remessa-row--muted"
                      : undefined
                  }
                >
                  <td>{formatRemessaBr(item.remessa)}</td>
                  <td>{formatDecimalString(item.previousQuantityUn)}</td>
                  <td>{formatDecimalString(item.currentQuantityUn)}</td>
                  <td>
                    {!unchanged || showAudit ? (
                      <span className={deltaClass}>
                        {formatDecimalString(item.deltaQuantityUn)}
                      </span>
                    ) : (
                      <span className="ppc-myweg-needs__delta">—</span>
                    )}
                  </td>
                  <td>
                    {remessaCtx ? (
                      <span className="ppc-myweg-needs__remessa-context">
                        {remessaCtx}
                      </span>
                    ) : (
                      <span className={situationBadgeClass(item.movement)}>
                        {movementLabel(item.movement)}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <button
          type="button"
          className="ppc-myweg-needs__audit-toggle"
          aria-expanded={showAudit}
          onClick={() => setShowAudit((value) => !value)}
        >
          {showAudit ? texts.hideAuditDetails : texts.showAuditDetails}
        </button>
        {showAudit ? (
          <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
            {texts.detailTotals}: {formatDecimalString(row.previousQuantityUn)} →{" "}
            {formatDecimalString(row.currentQuantityUn)} UN (
            <span
              className={observedDeltaToneClass({
                managerialStatus: managerial,
                situationOrMovement: row.situation,
              })}
            >
              {formatDecimalString(row.deltaQuantityUn)}
            </span>
            )
            {row.percentChange != null
              ? ` · ${formatPercentDisplay(row.percentChange)}`
              : null}
            {row.compatibleReductionUn != null
              ? ` · ${texts.columns.compatible}: ${formatDecimalString(row.compatibleReductionUn)} UN`
              : null}
          </p>
        ) : null}
      </div>

      <section
        className="ppc-myweg-needs__related-invoices"
        aria-label={texts.relatedInvoicesTitle}
      >
        <h4>
          {texts.relatedInvoicesTitle}
          <HelpTooltip
            content={helpTooltips.mywegNeedsInvoiceReconciliation}
            trigger="icon"
          />
        </h4>
        <p className="ppc-myweg-needs__related-invoices-note">
          {texts.relatedInvoicesNote}
        </p>
        {canLoadFiscal ? (
          <div className="ppc-myweg-needs__shifts-table-wrap">
            <table className="ppc-myweg-needs__shifts-table">
              <thead>
                <tr>
                  <th scope="col">{texts.fiscalColumns.invoice}</th>
                  <th scope="col">{texts.fiscalColumns.series}</th>
                  <th scope="col">{texts.fiscalColumns.documentDate}</th>
                  <th scope="col">{texts.fiscalColumns.material}</th>
                  <th scope="col">{texts.fiscalColumns.quantity}</th>
                </tr>
              </thead>
              <tbody>
                {fiscalLoading ? (
                  <tr>
                    <td colSpan={5}>{texts.fiscalLinesLoading}</td>
                  </tr>
                ) : fiscalError ? (
                  <tr>
                    <td colSpan={5}>{fiscalError}</td>
                  </tr>
                ) : fiscalLines.length === 0 ? (
                  <tr>
                    <td colSpan={5}>{texts.fiscalLinesEmpty}</td>
                  </tr>
                ) : (
                  fiscalLines.map((line) => (
                    <tr
                      key={`${line.observationId}|${line.id}|${line.sourceLineNo}`}
                    >
                      <td>{line.invoiceNumber}</td>
                      <td>{line.invoiceSeries}</td>
                      <td>{formatRemessaBr(line.documentDate)}</td>
                      <td>{line.materialWeg}</td>
                      <td>
                        {line.quantityUn != null
                          ? formatDecimalString(line.quantityUn)
                          : texts.unavailableValue}
                      </td>
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
        ) : (
          <p className="ppc-myweg-needs__evolution-note" role="status">
            {texts.fiscalLinesEmpty}
          </p>
        )}
      </section>

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

/** UI da Análise por produto sempre consulta com conciliação portal. */
const INVOICE_MODE: MyWegInvoiceMode = "portal";

export function MyWegProductConsolidationPanel({ fromId, toId, search }: Props) {
  const [page, setPage] = useState(1);
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
  }, [fromId, toId, search]);

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
      invoiceMode: INVOICE_MODE,
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
  }, [fromId, toId, search, page, refreshToken]);

  const coverageStatus = payload?.portalInvoices?.status;
  const pendingIngestion = coverageStatus === "pending_invoice_ingestion";

  useEffect(() => {
    if (!pendingIngestion) return;
    const timer = window.setInterval(() => {
      setRefreshToken((value) => value + 1);
    }, PENDING_POLL_MS);
    return () => window.clearInterval(timer);
  }, [pendingIngestion]);

  const columns = useMemo<DataTableColumn<MyWegProductConsolidation>[]>(() => {
    return [
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
        key: "residual",
        header: texts.columns.residualUnexplained,
        headerHint: helpTooltips.mywegNeedsAdjustedDelta,
        align: "right",
        render: (row) => {
          const residual = row.residualUnexplainedUn;
          if (residual == null || String(residual).trim() === "") {
            return texts.unavailableValue;
          }
          const isZero =
            String(residual).trim() === "0" ||
            String(residual).trim() === "0.0" ||
            String(residual).trim() === "0.00";
          if (isZero) {
            return (
              <span className="ppc-myweg-needs__delta ppc-myweg-needs__delta--invoiced">
                0
              </span>
            );
          }
          return (
            <span className="ppc-myweg-needs__delta ppc-myweg-needs__delta--down">
              {formatDecimalString(residual)}
            </span>
          );
        },
      },
      {
        key: "observed",
        header: texts.columns.observed,
        headerHint: helpTooltips.mywegNeedsObservedDelta,
        align: "right",
        render: (row) => {
          const value = row.observedDeltaUn ?? row.deltaQuantityUn;
          return (
            <span
              className={observedDeltaToneClass({
                managerialStatus: row.managerialStatus,
                situationOrMovement: row.situation,
              })}
            >
              {formatNullableDecimal(value, texts.unavailableValue)}
            </span>
          );
        },
      },
      {
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
      },
    ];
  }, [coverageStatus, selectedKey]);

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

  return (
    <section className="ppc-myweg-needs__products" aria-label={texts.title}>
      <header className="ppc-myweg-needs__products-header">
        <div className="ppc-myweg-needs__products-summary">
          <div className="ppc-myweg-needs__products-summary-copy">
            <h3 className="ppc-myweg-needs__shifts-title">
              <Layers size={18} strokeWidth={1.85} aria-hidden />
              {texts.title}
              <HelpTooltip
                content={helpTooltips.mywegNeedsInvoiceReconciliation}
                trigger="icon"
              />
            </h3>
            <p className="ppc-myweg-needs__evolution-note ppc-myweg-needs__evolution-note--compact">
              {texts.invoiceModeIntro}
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

        <button
          type="button"
          className="ppc-btn ppc-btn--secondary ppc-myweg-needs__refresh-btn"
          onClick={() => setRefreshToken((value) => value + 1)}
          disabled={loading}
        >
          <RefreshCw size={14} aria-hidden />
          {loading ? texts.refreshing : texts.refreshReconciliation}
        </button>
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

      {payload && status !== 403 ? (
        <DataTableSection
          title={texts.tableTitle}
          rows={payload.items}
          columns={columns}
          rowKey={(row) => row.productKey}
          emptyMessage={search ? copy.tableSection.emptyMessage : texts.empty}
          hideSearch
          interactive
          columnPreferencesKey="production-control:myweg-products:columns:v3"
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
        title={
          selected
            ? texts.detailHeading(productLabel(selected))
            : texts.title
        }
        onClose={closeDetail}
        closeAriaLabel={texts.detailCloseAria}
      >
        {selected ? (
          <ProductDetail
            row={selected}
            fromLabel={fromLabel}
            toLabel={toLabel}
            coverageStatus={coverageStatus}
          />
        ) : null}
      </HostContainedWideDialog>
    </section>
  );
}
