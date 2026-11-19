import { useCallback, useEffect, useMemo, useState } from "react";

import { exportPendingSuppliers, exportReturns, fetchShipment } from "../api/thirdPartyMaterialsApi";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { SectionError } from "../components/SectionError";
import { ShipmentDetailDialog } from "../components/ShipmentDetailDialog";
import { ShipmentFilters } from "../components/ShipmentFilters";
import { ShipmentsTable } from "../components/ShipmentsTable";
import { SummaryCards } from "../components/SummaryCards";
import { PendingSuppliersView } from "../components/PendingSuppliersView";
import { usePendingSuppliers } from "../hooks/usePendingSuppliers";
import { HELP_TOOLTIPS } from "../content/helpTooltips";
import { useShipments } from "../hooks/useShipments";
import { useSummary } from "../hooks/useSummary";
import type { Shipment, ThirdPartyMaterialsQuery } from "../types/thirdPartyMaterials";
import {
  DEFAULT_PAGE_SIZE,
  EMPTY_QUERY,
  MAX_PAGE_SIZE,
  hasUsefulScope,
} from "../types/thirdPartyMaterials";
import { getAccessToken } from "../api/httpClient";
import { canExport, resolveAuthorizedBranches } from "../utils/permissions";
import {
  BASE_PATH,
  parseUrlState,
  queryFromUrlState,
  replaceUrlState,
  type UrlState,
} from "../utils/urlState";

type MateriaisTerceirosPageProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  hasPermission?: (code: string) => boolean;
  isSuperadmin?: boolean;
};

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function MateriaisTerceirosPage({
  getAccessToken: getTokenFromHost,
  pathname,
  permissions,
  hasPermission,
  isSuperadmin,
}: MateriaisTerceirosPageProps) {
  const token = getTokenFromHost?.() ?? getAccessToken();
  const authorizedBranches = useMemo(
    () =>
      resolveAuthorizedBranches({
        token,
        permissions,
        hasPermission,
        isSuperadmin,
      }),
    [token, permissions, hasPermission, isSuperadmin],
  );
  const exportAllowed = useMemo(
    () => canExport({ token, permissions, hasPermission, isSuperadmin }),
    [token, permissions, hasPermission, isSuperadmin],
  );

  const initial = useMemo(() => {
    const search =
      typeof window !== "undefined" ? window.location.search : "";
    const parsed = parseUrlState(search);
    if (parsed.branch && !authorizedBranches.includes(parsed.branch)) {
      parsed.branch = authorizedBranches[0] ?? "";
    } else if (!parsed.branch && authorizedBranches.length === 1) {
      parsed.branch = authorizedBranches[0];
    }
    return parsed;
  }, [authorizedBranches]);

  const [filters, setFilters] = useState<UrlState>(initial);
  const [view, setView] = useState<"shipments" | "pending">("pending");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [selected, setSelected] = useState<Shipment | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    replaceUrlState(pathname || BASE_PATH, filters);
  }, [filters, pathname]);

  const query: ThirdPartyMaterialsQuery = useMemo(
    () => queryFromUrlState(filters),
    [filters],
  );
  const scoped = hasUsefulScope(query);
  const appliedQuery = scoped ? query : null;

  const summary = useSummary(view === "shipments" ? appliedQuery : null);
  const shipments = useShipments(view === "shipments" ? appliedQuery : null, page, pageSize);
  const pendingQuery = useMemo(() => query.branch ? {
    ...EMPTY_QUERY,
    branch: query.branch,
    partnerCode: query.partnerCode,
    partnerStore: query.partnerStore,
    product: query.product,
    includeTestProducts: query.includeTestProducts,
  } : null, [query.branch, query.partnerCode, query.partnerStore, query.product, query.includeTestProducts]);
  const pending = usePendingSuppliers(view === "pending" ? pendingQuery : null, page, pageSize);

  const handleFilterChange = useCallback((patch: Partial<ThirdPartyMaterialsQuery>) => {
    setFilters((current) => ({ ...current, ...patch }));
    setPage(1);
  }, []);

  const handleClear = useCallback(() => {
    setFilters({
      ...EMPTY_QUERY,
      branch: authorizedBranches[0] ?? "",
      shipmentRecno: "",
    });
    setPage(1);
    setSelected(null);
  }, [authorizedBranches]);

  const handleSelect = useCallback((row: Shipment) => {
    setSelected(row);
    setFilters((current) => ({ ...current, shipmentRecno: String(row.shipment_recno) }));
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelected(null);
    setFilters((current) => ({ ...current, shipmentRecno: "" }));
  }, []);

  useEffect(() => {
    const recno = Number(filters.shipmentRecno);
    if (!Number.isFinite(recno) || recno <= 0 || !filters.branch) return;
    if (selected?.shipment_recno === recno) return;

    const listed = shipments.data?.items.find((item) => item.shipment_recno === recno);
    if (listed) {
      setSelected(listed);
      return;
    }

    let cancelled = false;
    void fetchShipment(recno, filters.branch, filters.includeTestProducts)
      .then((item) => {
        if (!cancelled) setSelected(item);
      })
      .catch(() => {
        if (!cancelled) setSelected(null);
      });
    return () => {
      cancelled = true;
    };
  }, [
    filters.shipmentRecno,
    filters.branch,
    filters.includeTestProducts,
    selected?.shipment_recno,
    shipments.data,
  ]);

  const { reload: reloadSummary } = summary;
  const { reload: reloadShipments } = shipments;
  const { reload: reloadPending } = pending;
  const handleRefresh = useCallback(() => {
    reloadSummary();
    reloadShipments();
    reloadPending();
  }, [reloadSummary, reloadShipments, reloadPending]);

  const handlePageSizeChange = useCallback((next: number) => {
    setPageSize(Math.min(next, MAX_PAGE_SIZE));
    setPage(1);
  }, []);

  const handleExport = useCallback(
    async (format: "csv" | "xlsx") => {
      if (!appliedQuery) return;
      setExportError(null);
      setExporting(true);
      try {
        const result = await exportReturns(appliedQuery, format);
        downloadBlob(result.blob, result.filename);
      } catch (reason) {
        setExportError(reason instanceof Error ? reason.message : "Falha ao exportar.");
      } finally {
        setExporting(false);
      }
    },
    [appliedQuery],
  );

  return (
    <div className="dashboard-materiais-terceiros dashboard-page mt-page">
      <div className="mt-app-shell">
        <PageHeader
          title="Materiais de Terceiros"
          subtitle={HELP_TOOLTIPS.pageSubtitle}
          onRefresh={handleRefresh}
          refreshing={summary.refreshing || shipments.refreshing || pending.refreshing}
        />

        <div className="mt-view-switch" role="tablist" aria-label="Visões de materiais de terceiros">
          <button
            type="button"
            role="tab"
            aria-selected={view === "pending"}
            className={`mt-view-switch__item${view === "pending" ? " mt-view-switch__item--active" : ""}`}
            onClick={() => { setView("pending"); setPage(1); }}
          >
            Consolidado de pendências
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "shipments"}
            className={`mt-view-switch__item${view === "shipments" ? " mt-view-switch__item--active" : ""}`}
            onClick={() => { setView("shipments"); setPage(1); }}
          >
            Remessas e devoluções
          </button>
        </div>

        <ShipmentFilters
          mode={view}
          filters={query}
          authorizedBranches={authorizedBranches}
          onChange={handleFilterChange}
          onClear={handleClear}
        />

        {view === "pending" ? (
          <PendingSuppliersView
            data={pending.data}
            loading={pending.loading}
            error={pending.error}
            onRetry={pending.reload}
            query={pendingQuery}
            page={page}
            pageSize={pageSize}
            onPageChange={setPage}
            onExport={exportAllowed ? async (format) => {
              if (!pendingQuery) return;
              const result = await exportPendingSuppliers(pendingQuery, format);
              downloadBlob(result.blob, result.filename);
            } : undefined}
            onDrillDown={(item) => {
              setFilters((prev) => ({
                ...prev,
                branch: item.branch,
                partnerCode: item.supplier_code,
                partnerStore: item.supplier_store,
                product: item.product_code,
                onlyWithBalance: true,
                status: "",
                customerReference: "",
                receiptNumber: "",
                returnNumber: "",
                issuedFrom: "",
                issuedTo: "",
              }));
              setPage(1);
              setView("shipments");
            }}
          />
        ) : null}

        {view === "shipments" && !scoped ? (
          <EmptyState message="Informe a filial e um critério (parceiro, produto, NF, período ou somente saldo) para consultar as remessas." />
        ) : null}

        {view === "shipments" && scoped && summary.error ? (
          <SectionError
            title={summary.error.title}
            message={summary.error.message}
            onRetry={summary.error.retryable ? summary.reload : undefined}
          />
        ) : null}

        {view === "shipments" && scoped ? <SummaryCards summary={summary.data} loading={summary.loading} /> : null}

        {view === "shipments" && scoped && shipments.error ? (
          <SectionError
            title={shipments.error.title}
            message={shipments.error.message}
            onRetry={shipments.error.retryable ? shipments.reload : undefined}
          />
        ) : null}

        {exportError ? (
          <SectionError title="Exportação" message={exportError} />
        ) : null}

        {view === "shipments" && scoped ? (
          <ShipmentsTable
            rows={shipments.data?.items ?? []}
            loading={shipments.loading}
            refreshing={shipments.refreshing}
            page={page}
            pageSize={pageSize}
            total={shipments.data?.total ?? 0}
            onPageChange={setPage}
            onPageSizeChange={handlePageSizeChange}
            onSelect={handleSelect}
            canExport={exportAllowed}
            exporting={exporting}
            onExportCsv={() => void handleExport("csv")}
            onExportXlsx={() => void handleExport("xlsx")}
          />
        ) : null}
      </div>

      <ShipmentDetailDialog shipment={selected} onClose={handleCloseDetail} />
    </div>
  );
}
