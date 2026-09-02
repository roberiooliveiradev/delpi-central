import {
  AlertTriangle,
  Download,
  FileText,
  Percent,
  ShieldAlert,
  Truck,
  Wallet,
} from "lucide-react";
import { useMemo, useState } from "react";

import { FinBlockState } from "../components/FinBlockState";
import { FinWideDialog } from "../components/FinDialog";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { DataTable, DataTableSection, type DataTableColumn } from "../components/dataTableUi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useFreightDashboard, useFreightInconsistencies } from "../hooks/useFreight";
import { useSubplugins } from "../hooks/useSubplugins";
import type {
  FinancialBranch,
  FreightAllocation,
  FreightInconsistency,
  FreightInvoice,
} from "../types";
import { downloadExcel } from "../utils/exportExcel";
import { formatIsoDate, formatPeriodRange } from "../utils/formatDates";
import { formatInteger } from "../utils/formatNumbers";
import {
  formatDecimalCurrency,
  formatFreightLimit,
  formatFreightPercent,
  freightReasonLabels,
  freightRowClassName,
  freightSituationLabel,
  hasPartialBase,
} from "../utils/freightPresentation";
import { buildFinancialHref, replaceFinancialQuery } from "../utils/routeParser";

type FreightPageProps = {
  branch: FinancialBranch;
  issueStart: string | null;
  issueEnd: string | null;
  entryStart: string | null;
  entryEnd: string | null;
  supplierCode: string | null;
  invoiceDocument: string | null;
  freightDocument: string | null;
  situation: string | null;
  page: number;
};

type FreightQuery = FreightPageProps;

const SITUATION_OPTIONS = ["all", "normal", "above_limit", "inconsistent"] as const;
const DEFAULT_SORT_BY = "freight_percent";

function freightHref(query: FreightQuery): string {
  return buildFinancialHref({
    subpluginId: "freight",
    branch: query.branch,
    issueStart: query.issueStart,
    issueEnd: query.issueEnd,
    entryStart: query.entryStart,
    entryEnd: query.entryEnd,
    supplierCode: query.supplierCode,
    invoiceDocument: query.invoiceDocument,
    freightDocument: query.freightDocument,
    situation: query.situation,
    page: query.page,
  });
}

function invoiceKey(row: FreightInvoice): string {
  return [row.branch, row.invoiceDocument, row.invoiceSeries, row.supplierCode, row.supplierStore]
    .join("|");
}

export function FreightPage(props: FreightPageProps) {
  const { canExport } = useSubplugins();
  const [sortBy, setSortBy] = useState(DEFAULT_SORT_BY);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [openInvoiceKey, setOpenInvoiceKey] = useState<string | null>(null);
  const [showInconsistencies, setShowInconsistencies] = useState(false);
  const [inconsistencyPage, setInconsistencyPage] = useState(1);

  const { data, loading, error, reload } = useFreightDashboard({
    branch: props.branch,
    issueStart: props.issueStart,
    issueEnd: props.issueEnd,
    entryStart: props.entryStart,
    entryEnd: props.entryEnd,
    supplierCode: props.supplierCode,
    invoiceDocument: props.invoiceDocument,
    freightDocument: props.freightDocument,
    situation: props.situation,
    sortBy,
    sortDir,
    page: props.page,
  });

  const inconsistencies = useFreightInconsistencies({
    branch: props.branch,
    issueStart: props.issueStart,
    issueEnd: props.issueEnd,
    entryStart: props.entryStart,
    entryEnd: props.entryEnd,
    supplierCode: props.supplierCode,
    invoiceDocument: props.invoiceDocument,
    freightDocument: props.freightDocument,
    page: inconsistencyPage,
    enabled: showInconsistencies,
  });

  const hasPeriod = Boolean(
    (props.issueStart && props.issueEnd) || (props.entryStart && props.entryEnd),
  );

  /** Qualquer mudança de filtro volta para a primeira página da grade. */
  const patchQuery = (patch: Partial<FreightQuery>) => {
    setInconsistencyPage(1);
    replaceFinancialQuery(freightHref({ ...props, page: 1, ...patch }));
  };

  const toggleSort = (column: string) => {
    if (sortBy === column) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortBy(column);
    setSortDir("desc");
  };

  const reasonsByCode = useMemo(
    () => new Map(Object.entries(data?.reasonLabels ?? {})),
    [data?.reasonLabels],
  );

  const openInvoice = useMemo(
    () => (data?.items ?? []).find((row) => invoiceKey(row) === openInvoiceKey) ?? null,
    [data?.items, openInvoiceKey],
  );

  const summary = data?.summary;
  const period = formatPeriodRange(
    props.issueStart ?? props.entryStart,
    props.issueEnd ?? props.entryEnd,
  );

  const columns = useMemo<DataTableColumn<FreightInvoice>[]>(
    () => [
      { key: "branch", header: copy.freight.columns.branch, render: (row) => row.branch },
      {
        key: "invoice_document",
        header: copy.freight.columns.invoice,
        sortable: true,
        render: (row) => `${row.invoiceDocument}/${row.invoiceSeries}`,
      },
      {
        key: "supplier_name",
        header: copy.freight.columns.supplier,
        className: "delpi-ui-table__col--wide",
        sortable: true,
        render: (row) => (
          <div className="fin-customer-cell">
            <strong>{row.supplierName}</strong>
            <span>
              {row.supplierCode}/{row.supplierStore}
            </span>
          </div>
        ),
      },
      {
        key: "issue_date",
        header: copy.freight.columns.issueDate,
        sortable: true,
        render: (row) => formatIsoDate(row.issueDate),
      },
      {
        key: "entry_date",
        header: copy.freight.columns.entryDate,
        sortable: true,
        render: (row) => formatIsoDate(row.entryDate),
      },
      {
        key: "goods_value",
        header: copy.freight.columns.goodsValue,
        align: "right",
        sortable: true,
        render: (row) => formatDecimalCurrency(row.goodsValue),
      },
      {
        key: "freight_total",
        header: copy.freight.columns.freightTotal,
        align: "right",
        sortable: true,
        render: (row) => formatDecimalCurrency(row.freightTotal),
      },
      {
        key: "freight_percent",
        header: copy.freight.columns.freightPercent,
        align: "right",
        sortable: true,
        render: (row) => formatFreightPercent(row.freightPercent),
      },
      {
        key: "freight_limit",
        header: copy.freight.columns.freightLimit,
        align: "right",
        render: (row) => formatFreightLimit(row.freightLimit),
      },
      {
        key: "freight_document_count",
        header: copy.freight.columns.freightDocumentCount,
        align: "right",
        render: (row) => formatInteger(row.freightDocumentCount),
      },
      {
        key: "situation",
        header: copy.freight.columns.situation,
        render: (row) =>
          row.situation === "inconsistent"
            ? `${freightSituationLabel(row.situation)} — ${freightReasonLabels(
                row.reasonCodes,
                reasonsByCode,
              )}`
            : freightSituationLabel(row.situation),
      },
    ],
    [reasonsByCode],
  );

  const allocationColumns = useMemo<DataTableColumn<FreightAllocation>[]>(
    () => [
      {
        key: "freightDocument",
        header: copy.freight.detail.columns.freightDocument,
        render: (row) => (
          <div className="fin-customer-cell">
            <strong>
              {row.freightDocument}/{row.freightSeries}
            </strong>
            <span>{row.freightAccessKey}</span>
          </div>
        ),
      },
      {
        key: "carrier",
        header: copy.freight.detail.columns.carrier,
        render: (row) => `${row.carrierName} (${row.carrierCode}/${row.carrierStore})`,
      },
      {
        key: "freightIssueDate",
        header: copy.freight.detail.columns.freightIssueDate,
        render: (row) => formatIsoDate(row.freightIssueDate),
      },
      {
        key: "freightGrossValue",
        header: copy.freight.detail.columns.freightGrossValue,
        align: "right",
        render: (row) => formatDecimalCurrency(row.freightGrossValue),
      },
      {
        key: "allocationBase",
        header: copy.freight.detail.columns.allocationBase,
        align: "right",
        render: (row) =>
          openInvoice && hasPartialBase(openInvoice, row)
            ? `${formatDecimalCurrency(row.allocationBase)} · ${copy.freight.detail.partialBase}`
            : formatDecimalCurrency(row.allocationBase),
      },
      {
        key: "allocatedValue",
        header: copy.freight.detail.columns.allocatedValue,
        align: "right",
        render: (row) => formatDecimalCurrency(row.allocatedValue),
      },
      {
        key: "linkedInvoiceCount",
        header: copy.freight.detail.columns.linkedInvoiceCount,
        align: "right",
        render: (row) => formatInteger(row.linkedInvoiceCount),
      },
    ],
    [openInvoice],
  );

  /**
   * `duplicated_link` pode repetir o mesmo par NF x CT-e, então a chave da linha
   * vem da posição na página — os campos do vínculo não identificam sozinhos.
   */
  const inconsistencyKeys = useMemo(() => {
    const keys = new Map<FreightInconsistency, string>();
    (inconsistencies.data?.items ?? []).forEach((row, index) => {
      keys.set(row, `${row.reasonCode}-${row.invoiceDocument}-${row.freightDocument}-${index}`);
    });
    return keys;
  }, [inconsistencies.data?.items]);

  const inconsistencyColumns = useMemo<DataTableColumn<FreightInconsistency>[]>(
    () => [
      {
        key: "reason",
        header: copy.freight.inconsistencies.columns.reason,
        className: "delpi-ui-table__col--wide",
        render: (row) => row.reason,
      },
      { key: "branch", header: copy.freight.inconsistencies.columns.branch, render: (row) => row.branch },
      {
        key: "invoice",
        header: copy.freight.inconsistencies.columns.invoice,
        render: (row) => `${row.invoiceDocument}/${row.invoiceSeries}`,
      },
      {
        key: "supplier",
        header: copy.freight.inconsistencies.columns.supplier,
        render: (row) => `${row.supplierName} (${row.supplierCode})`,
      },
      {
        key: "freightDocument",
        header: copy.freight.inconsistencies.columns.freightDocument,
        render: (row) => `${row.freightDocument}/${row.freightSeries}`,
      },
      {
        key: "carrier",
        header: copy.freight.inconsistencies.columns.carrier,
        render: (row) => row.carrierName,
      },
      {
        key: "goodsValue",
        header: copy.freight.inconsistencies.columns.goodsValue,
        align: "right",
        render: (row) => formatDecimalCurrency(row.goodsValue),
      },
      {
        key: "freightGrossValue",
        header: copy.freight.inconsistencies.columns.freightGrossValue,
        align: "right",
        render: (row) => formatDecimalCurrency(row.freightGrossValue),
      },
    ],
    [],
  );

  /** Exporta o recorte visível: a grade é paginada no servidor. */
  const exportInvoices = () => {
    const rows = data?.items ?? [];
    if (!rows.length) {
      window.alert(copy.freight.exportEmpty);
      return;
    }
    void downloadExcel(
      {
        title: copy.freight.exportSheetTitle,
        columns: [
          { key: "branch", label: copy.freight.columns.branch },
          { key: "invoice", label: copy.freight.columns.invoice },
          { key: "supplier", label: copy.freight.columns.supplier },
          { key: "issueDate", label: copy.freight.columns.issueDate },
          { key: "entryDate", label: copy.freight.columns.entryDate },
          { key: "goodsValue", label: copy.freight.columns.goodsValue },
          { key: "freightTotal", label: copy.freight.columns.freightTotal },
          { key: "freightPercent", label: copy.freight.columns.freightPercent },
          { key: "freightLimit", label: copy.freight.columns.freightLimit },
          { key: "situation", label: copy.freight.columns.situation },
        ],
        rows: rows.map((row) => ({
          branch: row.branch,
          invoice: `${row.invoiceDocument}/${row.invoiceSeries}`,
          supplier: row.supplierName,
          issueDate: formatIsoDate(row.issueDate),
          entryDate: formatIsoDate(row.entryDate),
          goodsValue: Number(row.goodsValue),
          freightTotal: Number(row.freightTotal),
          freightPercent: row.freightPercent === null ? "" : Number(row.freightPercent),
          freightLimit: row.freightLimit === null ? copy.freight.noLimitBadge : Number(row.freightLimit),
          situation: freightSituationLabel(row.situation),
        })),
      },
      copy.freight.exportFileName,
    );
  };

  const exportInconsistencies = () => {
    const rows = inconsistencies.data?.items ?? [];
    if (!rows.length) {
      window.alert(copy.freight.inconsistencies.exportEmpty);
      return;
    }
    void downloadExcel(
      {
        title: copy.freight.inconsistencies.exportSheetTitle,
        columns: [
          { key: "reason", label: copy.freight.inconsistencies.columns.reason },
          { key: "branch", label: copy.freight.inconsistencies.columns.branch },
          { key: "invoice", label: copy.freight.inconsistencies.columns.invoice },
          { key: "supplier", label: copy.freight.inconsistencies.columns.supplier },
          { key: "freightDocument", label: copy.freight.inconsistencies.columns.freightDocument },
          { key: "carrier", label: copy.freight.inconsistencies.columns.carrier },
        ],
        rows: rows.map((row) => ({
          reason: row.reason,
          branch: row.branch,
          invoice: `${row.invoiceDocument}/${row.invoiceSeries}`,
          supplier: row.supplierName,
          freightDocument: `${row.freightDocument}/${row.freightSeries}`,
          carrier: row.carrierName,
        })),
      },
      copy.freight.inconsistencies.exportFileName,
    );
  };

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.freight.title}
        subtitle={copy.freight.subtitle}
        period={period}
        titleHint={helpTooltips.freight}
        branch={props.branch}
        subpluginId="freight"
        onBranchChange={(next) => patchQuery({ branch: next })}
        onRefresh={reload}
        refreshBusy={loading}
        actions={
          canExport && data ? (
            <button type="button" className="fin-icon-btn" onClick={exportInvoices}>
              <Download size={16} strokeWidth={1.75} aria-hidden />
              <span>{copy.freight.exportLabel}</span>
            </button>
          ) : null
        }
      />

      <div className="fin-toolbar">
        <div className="fin-filters" aria-label={copy.freight.filtersAria}>
          <label>
            {`${copy.freight.issuePeriodLabel} — ${copy.period.from}`}
            <input
              type="date"
              value={props.issueStart ?? ""}
              onChange={(event) => patchQuery({ issueStart: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.issuePeriodLabel} — ${copy.period.to}`}
            <input
              type="date"
              value={props.issueEnd ?? ""}
              onChange={(event) => patchQuery({ issueEnd: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.entryPeriodLabel} — ${copy.period.from}`}
            <input
              type="date"
              value={props.entryStart ?? ""}
              onChange={(event) => patchQuery({ entryStart: event.target.value || null })}
            />
          </label>
          <label>
            {`${copy.freight.entryPeriodLabel} — ${copy.period.to}`}
            <input
              type="date"
              value={props.entryEnd ?? ""}
              onChange={(event) => patchQuery({ entryEnd: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.supplierLabel}
            <input
              type="text"
              value={props.supplierCode ?? ""}
              onChange={(event) => patchQuery({ supplierCode: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.invoiceLabel}
            <input
              type="text"
              value={props.invoiceDocument ?? ""}
              onChange={(event) => patchQuery({ invoiceDocument: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.freightDocumentLabel}
            <input
              type="text"
              value={props.freightDocument ?? ""}
              onChange={(event) => patchQuery({ freightDocument: event.target.value || null })}
            />
          </label>
          <label>
            {copy.freight.situationLabel}
            <select
              value={props.situation ?? "all"}
              onChange={(event) => patchQuery({ situation: event.target.value })}
            >
              {SITUATION_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {copy.freight.situations[value]}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="fin-link-btn"
            onClick={() =>
              patchQuery({
                issueStart: null,
                issueEnd: null,
                entryStart: null,
                entryEnd: null,
                supplierCode: null,
                invoiceDocument: null,
                freightDocument: null,
                situation: null,
              })
            }
          >
            {copy.freight.clearFilters}
          </button>
        </div>
      </div>

      {hasPeriod ? null : (
        <FinBlockState block={undefined} empty emptyMessage={copy.freight.periodRequired} />
      )}

      {hasPeriod && loading && !data ? (
        <FinLoadingCard title={copy.freight.loading} description={copy.freight.loadingHint} />
      ) : null}

      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {summary && data ? (
        <>
          <div className="fin-kpi-grid" aria-label={copy.freight.kpiAria}>
            <FinKpiCard
              title={copy.freight.invoiceCountLabel}
              value={formatInteger(summary.invoiceCount)}
              icon={<FileText size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.freight.goodsTotalLabel}
              value={formatDecimalCurrency(summary.goodsTotal)}
              icon={<Wallet size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.freight.freightTotalLabel}
              value={formatDecimalCurrency(summary.freightTotal)}
              icon={<Truck size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.freight.freightPercentLabel}
              value={formatFreightPercent(summary.freightPercent)}
              icon={<Percent size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.freight.aboveLimitLabel}
              value={formatInteger(summary.aboveLimitCount)}
              icon={<AlertTriangle size={22} strokeWidth={1.75} />}
              comparisonTone={summary.aboveLimitCount > 0 ? "negative" : null}
            />
            <FinKpiCard
              title={copy.freight.inconsistentLabel}
              value={formatInteger(summary.inconsistentCount)}
              icon={<ShieldAlert size={22} strokeWidth={1.75} />}
              comparisonTone={summary.inconsistentCount > 0 ? "warning" : null}
            />
          </div>

          <p className="fin-scope-notice" role="note">
            {`${copy.freight.limitsTitle}: ${Object.entries(data.limits)
              .map(([code, limit]) => `${code} · ${formatFreightLimit(limit)}`)
              .join(" — ")}`}
          </p>

          {data.pagination.isComplete ? null : (
            <p className="fin-scope-notice" role="alert">
              {copy.freight.truncatedNotice}
            </p>
          )}

          <DataTableSection
            title={copy.freight.invoicesTitle}
            titleHint={helpTooltips.freightAllocation}
            hint={copy.freight.invoicesHint}
            columns={columns}
            rows={data.items}
            rowKey={invoiceKey}
            emptyMessage={copy.freight.invoicesEmpty}
            loading={loading}
            onRowClick={(row) => setOpenInvoiceKey(invoiceKey(row))}
            getRowClassName={(row) => freightRowClassName(row.situation)}
            hideSearch
            hidePageSizeSelect
            serverPagination={{
              page: data.pagination.page,
              pageSize: data.pagination.pageSize,
              total: data.pagination.totalItems,
              onPageChange: (nextPage: number) =>
                replaceFinancialQuery(freightHref({ ...props, page: nextPage })),
            }}
            serverSort={{
              sortKey: sortBy,
              sortDirection: sortDir,
              onSortChange: toggleSort,
            }}
          />

          <div className="fin-toolbar">
            <button
              type="button"
              className="fin-link-btn"
              aria-expanded={showInconsistencies}
              onClick={() => setShowInconsistencies((current) => !current)}
            >
              {showInconsistencies
                ? copy.freight.inconsistencies.hide
                : copy.freight.inconsistencies.show}
            </button>
            {showInconsistencies && canExport && inconsistencies.data ? (
              <button type="button" className="fin-icon-btn" onClick={exportInconsistencies}>
                <Download size={16} strokeWidth={1.75} aria-hidden />
                <span>{copy.freight.inconsistencies.exportLabel}</span>
              </button>
            ) : null}
          </div>

          {showInconsistencies ? (
            <>
              {inconsistencies.error ? (
                <div className="fin-state fin-state--error" role="alert">
                  {inconsistencies.error}
                </div>
              ) : null}
              {inconsistencies.data?.totalsByReason.length ? (
                <p className="fin-scope-notice" role="note">
                  {`${copy.freight.inconsistencies.totalsTitle}: ${inconsistencies.data.totalsByReason
                    .map((item) => `${item.reason} (${formatInteger(item.count)})`)
                    .join(" — ")}`}
                </p>
              ) : null}
              <DataTableSection
                title={copy.freight.inconsistencies.title}
                titleHint={helpTooltips.freightInconsistencies}
                hint={copy.freight.inconsistencies.hint}
                columns={inconsistencyColumns}
                rows={inconsistencies.data?.items ?? []}
                rowKey={(row) => inconsistencyKeys.get(row) ?? row.reasonCode}
                emptyMessage={copy.freight.inconsistencies.empty}
                loading={inconsistencies.loading}
                hideSearch
                hidePageSizeSelect
                serverPagination={
                  inconsistencies.data
                    ? {
                        page: inconsistencies.data.pagination.page,
                        pageSize: inconsistencies.data.pagination.pageSize,
                        total: inconsistencies.data.pagination.totalItems,
                        onPageChange: setInconsistencyPage,
                      }
                    : undefined
                }
              />
            </>
          ) : null}
        </>
      ) : null}

      {openInvoice ? (
        <FinWideDialog
          open
          title={copy.freight.detail.title}
          onClose={() => setOpenInvoiceKey(null)}
          closeAriaLabel={copy.freight.detail.close}
        >
          <dl className="fin-detail-grid">
            <div>
              <dt>{copy.freight.detail.invoice}</dt>
              <dd>{`${openInvoice.invoiceDocument}/${openInvoice.invoiceSeries}`}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.supplier}</dt>
              <dd>{`${openInvoice.supplierName} (${openInvoice.supplierCode}/${openInvoice.supplierStore})`}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.branch}</dt>
              <dd>{openInvoice.branch}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.issueDate}</dt>
              <dd>{formatIsoDate(openInvoice.issueDate)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.entryDate}</dt>
              <dd>{formatIsoDate(openInvoice.entryDate)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.goodsValue}</dt>
              <dd>{formatDecimalCurrency(openInvoice.goodsValue)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.freightTotal}</dt>
              <dd>{formatDecimalCurrency(openInvoice.freightTotal)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.freightPercent}</dt>
              <dd>{formatFreightPercent(openInvoice.freightPercent)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.freightLimit}</dt>
              <dd>{formatFreightLimit(openInvoice.freightLimit)}</dd>
            </div>
            <div>
              <dt>{copy.freight.detail.situation}</dt>
              <dd>{freightSituationLabel(openInvoice.situation)}</dd>
            </div>
            {openInvoice.reasonCodes.length ? (
              <div>
                <dt>{copy.freight.detail.reasons}</dt>
                <dd>{freightReasonLabels(openInvoice.reasonCodes, reasonsByCode)}</dd>
              </div>
            ) : null}
          </dl>

          <DataTable
            columns={allocationColumns}
            rows={openInvoice.allocations}
            rowKey={(row) => `${row.freightDocument}-${row.freightSeries}-${row.carrierCode}`}
            emptyMessage={copy.freight.detail.empty}
          />
        </FinWideDialog>
      ) : null}
    </div>
  );
}
