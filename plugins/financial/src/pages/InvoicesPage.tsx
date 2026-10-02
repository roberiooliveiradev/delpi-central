import { Download, Eye } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { ActionButton, FilePreviewModal } from "@delpi/plugin-ui/index";

import { downloadReceivedInvoiceDanfe, fetchReceivedInvoiceDanfe } from "../api/financialApi";
import { DataTableSection, type DataTableColumn } from "../components/dataTableUi";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useReceivedInvoices } from "../hooks/useReceivedInvoices";
import type { FinancialBranch, ReceivedInvoice } from "../types";
import { formatIsoDate } from "../utils/formatDates";
import { invoiceSearchHref } from "../utils/invoiceFilters";
import { buildFinancialHref, replaceFinancialQuery } from "../utils/routeParser";

type InvoicesPageProps = {
  branch: FinancialBranch;
  invoiceNumber: string | null;
  invoiceValue: string | null;
  supplierCnpj: string | null;
  page: number;
};

function formatCnpj(value: string): string {
  const digits = value.replace(/\D/g, "");
  if (digits.length !== 14) return value;
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function InvoiceFilterForm(props: Omit<InvoicesPageProps, "page">) {
  const [draftNumber, setDraftNumber] = useState(props.invoiceNumber ?? "");
  const [draftValue, setDraftValue] = useState(props.invoiceValue ?? "");
  const [draftCnpj, setDraftCnpj] = useState(props.supplierCnpj ?? "");

  const applyFilters = () => {
    replaceFinancialQuery(
      invoiceSearchHref({
        branch: props.branch,
        invoiceNumber: draftNumber,
        invoiceValue: draftValue,
        supplierCnpj: draftCnpj,
      }),
    );
  };

  const clearFilters = () => {
    replaceFinancialQuery(
      invoiceSearchHref({
        branch: props.branch,
        invoiceNumber: "",
        invoiceValue: "",
        supplierCnpj: "",
      }),
    );
  };

  return (
    <form
      className="fin-toolbar"
      onSubmit={(event) => {
        event.preventDefault();
        applyFilters();
      }}
    >
      <div className="fin-filters" aria-label={copy.invoices.filtersAria}>
        <label>
          {copy.invoices.invoiceNumber}
          <input
            type="text"
            name="invoiceNumber"
            value={draftNumber}
            onChange={(event) => setDraftNumber(event.target.value)}
          />
        </label>
        <label>
          {copy.invoices.value}
          <input
            type="text"
            name="invoiceValue"
            inputMode="decimal"
            value={draftValue}
            onChange={(event) => setDraftValue(event.target.value)}
          />
        </label>
        <label>
          {copy.invoices.supplierCnpj}
          <input
            type="text"
            name="supplierCnpj"
            value={draftCnpj}
            onChange={(event) => setDraftCnpj(event.target.value)}
          />
        </label>
        <button type="submit" className="fin-link-btn">
          {copy.invoices.search}
        </button>
        <button type="button" className="fin-link-btn" onClick={clearFilters}>
          {copy.invoices.clear}
        </button>
      </div>
    </form>
  );
}

export function InvoicesPage(props: InvoicesPageProps) {
  const [preview, setPreview] = useState<ReceivedInvoice | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const { data, loading, error, reload } = useReceivedInvoices({
    invoiceNumber: props.invoiceNumber,
    invoiceValue: props.invoiceValue,
    supplierCnpj: props.supplierCnpj,
    page: props.page,
  });

  const goToPage = (page: number) => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "invoices",
        branch: props.branch,
        invoiceNumber: props.invoiceNumber,
        invoiceValue: props.invoiceValue,
        supplierCnpj: props.supplierCnpj,
        page,
      }),
    );
  };

  const downloadDanfe = useCallback(async (row: ReceivedInvoice) => {
    setDownloadError(null);
    setDownloadingId(row.documentId);
    try {
      await downloadReceivedInvoiceDanfe(row.documentId, row.accessKey, row.branchCode);
    } catch (downloadFailure) {
      setDownloadError(
        downloadFailure instanceof Error && downloadFailure.message.trim()
          ? downloadFailure.message
          : copy.invoices.downloadError,
      );
    } finally {
      setDownloadingId(null);
    }
  }, []);

  const previewSource = useMemo(() => {
    if (!preview) return null;
    const documentId = preview.documentId;
    const accessKey = preview.accessKey;
    const branch = preview.branchCode;
    return () => fetchReceivedInvoiceDanfe(documentId, accessKey, branch);
  }, [preview]);

  const columns = useMemo<DataTableColumn<ReceivedInvoice>[]>(
    () => [
      {
        key: "invoiceNumber",
        header: copy.invoices.columns.invoice,
        render: (row) => (
          <span title={row.accessKey ? `${copy.invoices.accessKeyHint}: ${row.accessKey}` : undefined}>
            {row.invoiceNumber || "—"}
          </span>
        ),
      },
      {
        key: "series",
        header: copy.invoices.columns.series,
        render: (row) => row.series || "—",
      },
      {
        key: "emissionAt",
        header: copy.invoices.columns.emission,
        render: (row) => formatIsoDate(row.emissionAt),
      },
      {
        key: "issuerName",
        header: copy.invoices.columns.supplier,
        className: "delpi-ui-table__col--wide",
        render: (row) => (
          <div className="fin-customer-cell">
            <strong>{row.issuerName || "—"}</strong>
            {row.issuerCnpj ? <span>{formatCnpj(row.issuerCnpj)}</span> : null}
          </div>
        ),
      },
      {
        key: "amount",
        header: copy.invoices.columns.amount,
        align: "right",
        render: (row) => row.amountFormatted || row.amount || "—",
      },
      {
        key: "manifestation",
        header: copy.invoices.columns.manifestation,
        render: (row) => row.manifestationDescription || row.manifestationCode || "—",
      },
      {
        key: "actions",
        header: copy.invoices.columns.actions,
        render: (row) => {
          const available = row.danfeAvailable && Boolean(row.documentId) && row.accessKey.length === 44;
          const viewLabel = available ? copy.invoices.viewDanfe : copy.invoices.danfeUnavailable;
          const downloadLabel = available ? copy.invoices.downloadDanfe : copy.invoices.danfeUnavailable;
          return (
            <div className="fin-row-actions">
              <button
                type="button"
                className="fin-icon-btn"
                disabled={!available}
                title={viewLabel}
                aria-label={viewLabel}
                onClick={() => {
                  if (available) setPreview(row);
                }}
              >
                <Eye size={16} strokeWidth={1.75} aria-hidden />
                <span>{viewLabel}</span>
              </button>
              <button
                type="button"
                className="fin-icon-btn"
                disabled={!available || downloadingId === row.documentId}
                title={downloadLabel}
                aria-label={downloadLabel}
                onClick={() => {
                  if (available) void downloadDanfe(row);
                }}
              >
                <Download size={16} strokeWidth={1.75} aria-hidden />
                <span>{downloadLabel}</span>
              </button>
            </div>
          );
        },
      },
    ],
    [downloadingId, downloadDanfe],
  );

  const items = data?.items ?? [];

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.invoices.title}
        subtitle={copy.invoices.subtitle}
        titleHint={helpTooltips.invoices}
        branch={props.branch}
        subpluginId="invoices"
        showBranchSelector={false}
        onRefresh={reload}
        refreshBusy={loading}
      />

      <InvoiceFilterForm
        key={`${props.invoiceNumber ?? ""}|${props.invoiceValue ?? ""}|${props.supplierCnpj ?? ""}`}
        branch={props.branch}
        invoiceNumber={props.invoiceNumber}
        invoiceValue={props.invoiceValue}
        supplierCnpj={props.supplierCnpj}
      />

      {downloadError ? (
        <div className="fin-state fin-state--error" role="alert">
          {downloadError}
        </div>
      ) : null}

      {loading && !error ? <p role="status">{copy.invoices.loading}</p> : null}

      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : (
        <DataTableSection
          title={copy.invoices.title}
          titleHint={helpTooltips.invoices}
          columns={columns}
          rows={items}
          rowKey={(row) => row.documentId || row.accessKey || row.invoiceNumber}
          emptyMessage={copy.invoices.empty}
          loading={loading}
          hideSearch
          hidePageSizeSelect
          serverPagination={
            data
              ? {
                  page: data.pagination.page,
                  pageSize: data.pagination.pageSize,
                  total: data.pagination.totalItems,
                  onPageChange: goToPage,
                }
              : undefined
          }
        />
      )}
      <FilePreviewModal
        open={preview != null}
        title={preview ? `DANFE ${preview.invoiceNumber}` : "DANFE"}
        onClose={() => setPreview(null)}
        source={previewSource}
        mimeType="application/pdf"
        declaredType="pdf"
        fileName={preview ? `NFe-${preview.accessKey}.pdf` : null}
        portalScopeClassName="dashboard-financial"
        labels={{
          loading: copy.invoices.previewLoading,
          loadFailed: copy.invoices.previewError,
        }}
        headerActions={
          preview ? (
            <ActionButton
              type="button"
              variant="ghost"
              disabled={downloadingId === preview.documentId}
              onClick={() => void downloadDanfe(preview)}
            >
              {downloadingId === preview.documentId ? "Baixando…" : copy.invoices.downloadDanfe}
            </ActionButton>
          ) : null
        }
      />
    </div>
  );
}
