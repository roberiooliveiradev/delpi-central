import {
  createDashboardLoadingActivityCard,
  NavigationCard,
  navigationCardBemClasses,
} from "@delpi/plugin-ui/index";
import { Layers, PackageMinus, PackageX } from "lucide-react";
import { useEffect, useState } from "react";

import { DataTableSection } from "../components/dataTableUi";
import { FinishedProductShortagePanel } from "../components/FinishedProductShortagePanel";
import { MaterialsDetailModal } from "../components/MaterialsDetailModal";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { MATERIALS_DEFAULT_FILTERS, useMaterials, type MaterialsFilters } from "../hooks/useMaterials";
import type {
  MaterialsIssueId,
  MaterialsLine,
  MaterialsSetStatus,
  MaterialsShortageLine,
  PpcBranch,
} from "../types";
import {
  asMaterialsSetStatus,
  asMaterialsWorkspace,
  finishedProductShortageQueryCode,
} from "../utils/finishedProductShortageQuery";
import { downloadMaterialsExcel } from "../utils/materialsExcel";
import { formatIsoDate } from "../utils/formatIsoDate";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import {
  buildPpcHref,
  navigatePpc,
  readMaterialsDetailDeepLink,
} from "../utils/routeParser";

const navCardClassNames = navigationCardBemClasses("ppc");

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.materials.loading,
  },
});

const severityLabel: Record<string, string> = {
  critical: copy.problemAnalysis.critical,
  attention: copy.problemAnalysis.attention,
  ok: copy.problemAnalysis.ok,
};

type MaterialsPageProps = {
  branch: PpcBranch;
  issue: string | null;
  search: string | null;
  status: string | null;
  requestNumber: string | null;
  requestItem: string | null;
};

function defaultSortFor(view: Exclude<MaterialsIssueId, "pa-shortage">): string {
  return view === "shortage" ? "shortage_quantity" : "required_date";
}

function issueIcon(id: MaterialsIssueId) {
  if (id === "shortage") return <PackageX size={20} strokeWidth={1.75} />;
  if (id === "pa-shortage") return <Layers size={20} strokeWidth={1.75} />;
  return <PackageMinus size={20} strokeWidth={1.75} />;
}

function issueEyebrow(card: { id: MaterialsIssueId; severity: string; product_count?: number }) {
  const severity = severityLabel[card.severity] ?? "";
  if (card.id === "pa-shortage" || card.product_count == null) {
    return `${severity} · ${copy.materials.consultEyebrow}`;
  }
  return `${severity} · ${copy.materials.issueCount(card.product_count)}`;
}

export function MaterialsPage({
  branch,
  issue,
  search,
  status,
  requestNumber,
  requestItem,
}: MaterialsPageProps) {
  const workspace = asMaterialsWorkspace(issue);
  const tableView: Exclude<MaterialsIssueId, "pa-shortage"> =
    workspace === "shortage" ? "shortage" : "excess";
  const [filters, setFilters] = useState<MaterialsFilters>({
    ...MATERIALS_DEFAULT_FILTERS,
    view: tableView,
    sort: defaultSortFor(tableView),
    search: workspace === "pa-shortage" ? "" : (search ?? requestNumber ?? ""),
  });
  const [searchDraft, setSearchDraft] = useState(filters.search);
  const [selected, setSelected] = useState<MaterialsLine | MaterialsShortageLine | null>(null);
  const [paDraft, setPaDraft] = useState(workspace === "pa-shortage" ? (search ?? "") : "");
  const [paQuery, setPaQuery] = useState(finishedProductShortageQueryCode(workspace, search));
  const [setStatus, setSetStatus] = useState<MaterialsSetStatus>(asMaterialsSetStatus(status));
  const { data, loading, refreshing, error, reload } = useMaterials(branch, filters);
  const materials = copy.materials;

  useEffect(() => {
    const nextWorkspace = asMaterialsWorkspace(issue);
    const nextTable: Exclude<MaterialsIssueId, "pa-shortage"> =
      nextWorkspace === "shortage" ? "shortage" : "excess";
    setFilters((current) => ({
      ...current,
      view: nextTable,
      sort: current.view === nextTable ? current.sort : defaultSortFor(nextTable),
      search: nextWorkspace === "pa-shortage" ? "" : current.search,
      page: 1,
    }));
    setSelected(null);
  }, [branch, issue]);

  useEffect(() => {
    if (asMaterialsWorkspace(issue) !== "pa-shortage") return;
    const nextDraft = search ?? "";
    setPaDraft(nextDraft);
    setPaQuery(finishedProductShortageQueryCode("pa-shortage", nextDraft));
    setSetStatus(asMaterialsSetStatus(status));
  }, [branch, issue, search, status]);

  useEffect(() => {
    if (workspace === "pa-shortage") return;
    const timer = window.setTimeout(() => {
      setFilters((current) =>
        current.search === searchDraft ? current : { ...current, search: searchDraft, page: 1 },
      );
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchDraft, workspace]);

  useEffect(() => {
    if (workspace === "pa-shortage") {
      navigatePpc(
        buildPpcHref({
          subpluginId: "materials",
          branch,
          materialsIssue: "pa-shortage",
          materialsSearch: paQuery || null,
          materialsStatus: setStatus === "all" ? null : setStatus,
        }),
      );
      return;
    }
    navigatePpc(
      buildPpcHref({
        subpluginId: "materials",
        branch,
        materialsIssue: filters.view,
        materialsSearch: filters.search || null,
        requestNumber:
          selected && "request_number" in selected ? selected.request_number : null,
        requestItem: selected && "request_item" in selected ? selected.request_item : null,
      }),
    );
  }, [branch, filters, paQuery, selected, setStatus, workspace]);

  useEffect(() => {
    if (!data || selected || workspace === "pa-shortage" || filters.view !== "excess") return;
    const { requestNumber: requestFromUrl, requestItem: itemFromUrl } =
      readMaterialsDetailDeepLink(window.location.search);
    if (!requestFromUrl) return;
    const match = data.items.find(
      (row): row is MaterialsLine =>
        "request_number" in row &&
        row.request_number === requestFromUrl &&
        (!itemFromUrl || row.request_item === itemFromUrl),
    );
    if (match) setSelected(match);
  }, [data, selected, search, requestNumber, requestItem, filters.view, workspace]);

  const handleCloseDetail = () => {
    setSelected(null);
  };

  const patch = (changes: Partial<MaterialsFilters>) =>
    setFilters((current) => ({ ...current, page: 1, ...changes }));

  const openIssue = (id: MaterialsIssueId) => {
    setSelected(null);
    if (id === "pa-shortage") {
      navigatePpc(
        buildPpcHref({
          subpluginId: "materials",
          branch,
          materialsIssue: "pa-shortage",
          materialsSearch: paQuery || null,
          materialsStatus: setStatus === "all" ? null : setStatus,
        }),
      );
      return;
    }
    setFilters((current) => ({
      ...current,
      view: id,
      sort: defaultSortFor(id),
      page: 1,
    }));
  };

  const issues = data?.issues ?? [];
  const view = workspace === "pa-shortage" ? "pa-shortage" : (data?.view ?? filters.view);
  const rows = data?.items ?? [];
  const isShortage = view === "shortage";

  const excessColumns = [
    {
      key: "request_number",
      header: materials.columns.request,
      render: (row: MaterialsLine) => `${row.request_number}/${row.request_item}`,
    },
    {
      key: "product_code",
      header: materials.columns.product,
      render: (row: MaterialsLine) =>
        row.product_description ? `${row.product_code} · ${row.product_description}` : row.product_code,
    },
    {
      key: "open_quantity",
      header: materials.columns.open,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.open_quantity),
    },
    {
      key: "available_stock",
      header: materials.columns.stock,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.available_stock),
    },
    {
      key: "safety_stock",
      header: materials.columns.safety,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.safety_stock),
    },
    {
      key: "open_purchase_order_quantity",
      header: materials.columns.orders,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.open_purchase_order_quantity),
    },
    {
      key: "open_commitment_quantity",
      header: materials.columns.commitments,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.open_commitment_quantity),
    },
    {
      key: "projected_balance",
      header: materials.columns.projected,
      align: "right" as const,
      render: (row: MaterialsLine) => formatOpQuantity(row.projected_balance),
    },
    {
      key: "required_date",
      header: materials.columns.required,
      render: (row: MaterialsLine) => (row.required_date ? formatIsoDate(row.required_date) : "—"),
    },
  ];

  const shortageColumns = [
    {
      key: "product_code",
      header: materials.columns.product,
      render: (row: MaterialsShortageLine) =>
        row.product_description ? `${row.product_code} · ${row.product_description}` : row.product_code,
    },
    {
      key: "safety_stock",
      header: materials.columns.safety,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.safety_stock),
    },
    {
      key: "available_stock",
      header: materials.columns.stock,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.available_stock),
    },
    {
      key: "open_purchase_order_quantity",
      header: materials.columns.orders,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.open_purchase_order_quantity),
    },
    {
      key: "open_commitment_quantity",
      header: materials.columns.commitments,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.open_commitment_quantity),
    },
    {
      key: "projected_balance",
      header: materials.columns.projected,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.projected_balance),
    },
    {
      key: "open_sc1_quantity",
      header: materials.columns.openSc1,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.open_sc1_quantity),
    },
    {
      key: "shortage_quantity",
      header: materials.columns.shortage,
      align: "right" as const,
      render: (row: MaterialsShortageLine) => formatOpQuantity(row.shortage_quantity),
    },
  ];

  return (
    <div className="ppc-page-stack ppc-page-stack--demand">
      <PpcWorkspaceHeader
        title={materials.title}
        subtitle={materials.subtitle}
        titleHint={helpTooltips.materials}
        branch={branch}
        subpluginId="materials"
        materialsIssue={workspace}
        materialsSearch={workspace === "pa-shortage" ? paQuery || null : filters.search || null}
        materialsStatus={workspace === "pa-shortage" && setStatus !== "all" ? setStatus : null}
        onRefresh={reload}
        refreshBusy={refreshing}
      />

      {loading ? (
        <LoadingCard title={materials.loading} description={materials.loadingHint} />
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || materials.loadError}
        </div>
      ) : null}

      {data ? (
        <>
          <section className="ppc-detectors__grid" aria-label={materials.issuesAria}>
            {issues.map((card) => (
              <div
                key={card.id}
                className="ppc-detector-card"
                data-severity={card.severity}
                data-active={card.id === view ? "true" : undefined}
              >
                <NavigationCard
                  classNames={navCardClassNames}
                  icon={issueIcon(card.id)}
                  eyebrow={issueEyebrow(card)}
                  title={card.title}
                  description={card.description}
                  onClick={() => openIssue(card.id)}
                />
              </div>
            ))}
          </section>

          {workspace === "pa-shortage" ? (
            <FinishedProductShortagePanel
              branch={branch}
              productQuery={paQuery}
              draft={paDraft}
              status={setStatus}
              didactic={data.didactic}
              onDraftChange={setPaDraft}
              onSubmit={setPaQuery}
              onStatusChange={setSetStatus}
            />
          ) : isShortage ? (
            <DataTableSection<MaterialsShortageLine>
              title={materials.shortageTableTitle}
              hint={materials.shortageTableHint}
              columns={shortageColumns}
              rows={rows as MaterialsShortageLine[]}
              rowKey={(row) => row.id}
              loading={loading}
              refreshing={refreshing}
              emptyMessage={materials.shortageEmpty}
              searchPlaceholder={materials.shortageSearchPlaceholder}
              columnPreferencesKey="production-control:materials:shortage-columns:v1"
              onRowClick={setSelected}
              serverSearch={{ value: searchDraft, onChange: setSearchDraft }}
              serverSort={{
                sortKey: filters.sort,
                sortDirection: filters.direction,
                onSortChange: (columnKey) =>
                  patch({
                    sort: columnKey,
                    direction:
                      filters.sort === columnKey && filters.direction === "asc" ? "desc" : "asc",
                  }),
              }}
              serverPagination={{
                page: data.pagination.page,
                pageSize: data.pagination.page_size,
                total: data.pagination.total,
                onPageChange: (page) => setFilters((current) => ({ ...current, page })),
                onPageSizeChange: (pageSize) => patch({ pageSize }),
              }}
              excelExport={{
                onExport: () =>
                  downloadMaterialsExcel(rows, view, materials.exportFileName(branch, view)),
                disabled: rows.length === 0,
              }}
            />
          ) : (
            <DataTableSection<MaterialsLine>
              title={materials.tableTitle}
              hint={materials.tableHint}
              columns={excessColumns}
              rows={rows as MaterialsLine[]}
              rowKey={(row) => row.id}
              loading={loading}
              refreshing={refreshing}
              emptyMessage={materials.empty}
              searchPlaceholder={materials.searchPlaceholder}
              columnPreferencesKey="production-control:materials:columns:v2"
              onRowClick={setSelected}
              serverSearch={{ value: searchDraft, onChange: setSearchDraft }}
              serverSort={{
                sortKey: filters.sort,
                sortDirection: filters.direction,
                onSortChange: (columnKey) =>
                  patch({
                    sort: columnKey,
                    direction:
                      filters.sort === columnKey && filters.direction === "asc" ? "desc" : "asc",
                  }),
              }}
              serverPagination={{
                page: data.pagination.page,
                pageSize: data.pagination.page_size,
                total: data.pagination.total,
                onPageChange: (page) => setFilters((current) => ({ ...current, page })),
                onPageSizeChange: (pageSize) => patch({ pageSize }),
              }}
              excelExport={{
                onExport: () =>
                  downloadMaterialsExcel(rows, view, materials.exportFileName(branch, view)),
                disabled: rows.length === 0,
              }}
            />
          )}
        </>
      ) : null}

      <MaterialsDetailModal line={selected} onClose={handleCloseDetail} />
    </div>
  );
}
