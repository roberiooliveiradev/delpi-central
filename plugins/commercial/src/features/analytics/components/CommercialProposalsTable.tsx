import { runTabularExport, type DataTableColumn } from "@delpi/plugin-ui/index";
import { useMemo } from "react";

import {
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEntityLink,
  CommercialStatusBadge,
  CommercialTableColumnVisibilityMenu,
  CommercialTableFontSizeControls,
  CommercialTabularExportButtons,
} from "../../../app/commercialUi";
import {
  buildAnalyticsOpportunityDetailHref,
  navigateAnalyticsOpportunityDetail,
} from "../../../app/pluginNavigation";
import { opportunityLinkTitle } from "../../../content/entityLinkHints";
import { CM_HELP } from "../../../content/helpTooltips";
import type {
  CommercialProposal,
  CommercialProposalStatusCategory,
} from "../../../types/analytics";
import {
  PROPOSALS_DOCUMENTS_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";
import { formatDisplayDate } from "../../../utils/dates";
import type { TableSortDirection } from "../../../utils/sortTableRows";
import { useOpportunitiesTablePreferences } from "../hooks/useOpportunitiesTablePreferences";
import {
  OPPORTUNITY_LIST_COLUMNS_STORAGE_KEY,
  OPPORTUNITY_LIST_EMPTY_FALLBACK_KEYS,
  OPPORTUNITY_LIST_FONT_STORAGE_KEY,
  resolveOpportunityListColumnCatalog,
} from "../utils/opportunityTableColumns";
import { OpenProposalFromOpportunityButton } from "./OpenProposalFromOpportunityButton";

export type CommercialProposalsTableOptions = {
  basePath: string;
  /** Query string preserved when opening OV detail (back navigation). */
  detailSearch?: string;
  /** When true, omit Cliente column (account context). */
  hideCustomerColumn?: boolean;
  /** When true, omit Vendedor column (account context). */
  hideSellerColumn?: boolean;
  /** CTA Abrir proposta (ADY) quando o usuário tem proposals.view. */
  showOpenProposal?: boolean;
};

function statusBadgeVariant(
  category: CommercialProposalStatusCategory | null | undefined,
): "success" | "danger" | "info" | "neutral" {
  switch (category) {
    case "won":
      return "success";
    case "lost":
      return "danger";
    case "open":
      return "info";
    default:
      return "neutral";
  }
}

function sellerDisplay(row: CommercialProposal): string {
  return (row.seller_name || row.seller_code || "").trim() || "—";
}

/** Colunas canônicas da lista de OVs (página global e Conta). */
export function buildCommercialProposalColumns(
  options: CommercialProposalsTableOptions,
): DataTableColumn<CommercialProposal>[] {
  const columns: DataTableColumn<CommercialProposal>[] = [
    {
      key: "ov",
      header: "OV",
      sortable: true,
      sortValue: (row) => row.proposal_number,
      interactive: true,
      rowClick: "stop",
      render: (row) => {
        const href = buildAnalyticsOpportunityDetailHref(row.proposal_number, {
          basePath: options.basePath,
          search: options.detailSearch,
        });
        if (!href) {
          return <span className="cm-proposals-table__ov">{row.proposal_number}</span>;
        }
        return (
          <CommercialEntityLink
            href={href}
            title={opportunityLinkTitle(row.proposal_number)}
            className="cm-link-button cm-proposals-table__ov"
            onNavigate={() =>
              navigateAnalyticsOpportunityDetail(row.proposal_number, {
                basePath: options.basePath,
                search: options.detailSearch,
              })
            }
          >
            {row.proposal_number}
          </CommercialEntityLink>
        );
      },
    },
    {
      key: "rev",
      header: "Rev.",
      sortable: true,
      sortValue: (row) => row.revision,
      render: (row) => row.revision || "—",
    },
  ];

  if (!options.hideCustomerColumn) {
    columns.push({
      key: "customer",
      header: "Cliente",
      sortable: true,
      sortValue: (row) => row.customer_code,
      render: (row) => row.customer_code || "—",
    });
  }

  if (!options.hideSellerColumn) {
    columns.push({
      key: "seller",
      header: "Vendedor",
      sortable: false,
      render: (row) => sellerDisplay(row),
    });
  }

  columns.push(
    {
      key: "status",
      header: "Status",
      sortable: true,
      sortValue: (row) => row.status_label || row.status_code || "",
      render: (row) => (
        <CommercialStatusBadge
          label={row.status_label || row.status_code || "—"}
          variant={statusBadgeVariant(row.status_category)}
        />
      ),
    },
    {
      key: "stage",
      header: "Etapa",
      sortable: true,
      sortValue: (row) => row.stage,
      render: (row) => row.stage || "—",
    },
    {
      key: "date",
      header: "Data",
      sortable: true,
      sortValue: (row) => row.proposal_date,
      render: (row) => formatDisplayDate(row.proposal_date),
    },
  );

  if (options.showOpenProposal) {
    columns.push({
      key: "proposal-doc",
      header: "Proposta",
      interactive: true,
      rowClick: "stop",
      render: (row) => (
        <OpenProposalFromOpportunityButton
          basePath={options.basePath}
          opportunityNumber={row.proposal_number}
        />
      ),
    });
  }

  return columns;
}

type CommercialProposalsTableProps = CommercialProposalsTableOptions & {
  rows: CommercialProposal[];
  onRowClick?: (row: CommercialProposal) => void;
  /** Server-side sort — rows must already be ordered by the API. */
  sortKey: string;
  sortDirection: TableSortDirection;
  onSortChange: (columnKey: string) => void;
};

export function CommercialProposalsTable({
  rows,
  basePath,
  detailSearch,
  hideCustomerColumn,
  hideSellerColumn,
  showOpenProposal,
  onRowClick,
  sortKey,
  sortDirection,
  onSortChange,
}: CommercialProposalsTableProps) {
  const columnCatalog = useMemo(
    () =>
      resolveOpportunityListColumnCatalog({
        hideCustomerColumn,
        hideSellerColumn,
        showOpenProposal,
      }),
    [hideCustomerColumn, hideSellerColumn, showOpenProposal],
  );

  const {
    visibility,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    resetColumns,
    filterColumns,
    tableStyle,
    fontSize,
    increaseFont,
    decreaseFont,
    resetFont,
    canIncreaseFont,
    canDecreaseFont,
    isDefaultFont,
  } = useOpportunitiesTablePreferences({
    columnsStorageKey: OPPORTUNITY_LIST_COLUMNS_STORAGE_KEY,
    fontSizeStorageKey: OPPORTUNITY_LIST_FONT_STORAGE_KEY,
    columns: columnCatalog,
    emptyFallbackKeys: [...OPPORTUNITY_LIST_EMPTY_FALLBACK_KEYS],
  });

  const baseColumns = useMemo(
    () =>
      buildCommercialProposalColumns({
        basePath,
        detailSearch,
        hideCustomerColumn,
        hideSellerColumn,
        showOpenProposal,
      }),
    [basePath, detailSearch, hideCustomerColumn, hideSellerColumn, showOpenProposal],
  );
  const columns = useMemo(
    () => filterColumns(withColumnHelp(baseColumns, PROPOSALS_DOCUMENTS_COLUMN_HELP)),
    [baseColumns, filterColumns],
  );

  return (
    <div style={tableStyle}>
      <CommercialDataListToolbar
        style={tableStyle}
        hint={
          <span className="delpi-ui-section-hint-label">
            {visibleColumnCount} coluna(s) · {rows.length.toLocaleString("pt-BR")} linha(s)
          </span>
        }
        actions={
          <>
            <CommercialTabularExportButtons
              compact
              disabled={!rows.length}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title: "Oportunidades",
                    columns: columnCatalog.map((column) => ({
                      key: column.key,
                      label: column.label,
                    })),
                    rows: rows.map((row) => ({
                      ov: row.proposal_number,
                      rev: row.revision || "",
                      customer: row.customer_code || "",
                      seller: sellerDisplay(row),
                      status: row.status_label || row.status_code || "",
                      stage: row.stage || "",
                      date: formatDisplayDate(row.proposal_date),
                      "proposal-doc": "",
                    })),
                  },
                });
              }}
            />
            <CommercialTableFontSizeControls
              fontSize={fontSize}
              onIncrease={increaseFont}
              onDecrease={decreaseFont}
              onReset={resetFont}
              canIncrease={canIncreaseFont}
              canDecrease={canDecreaseFont}
              isDefault={isDefaultFont}
            />
            <CommercialTableColumnVisibilityMenu
              columns={orderedColumns}
              visibility={visibility}
              onToggleColumn={setColumnVisible}
              onReorderColumns={reorderColumns}
              onReset={resetColumns}
              labels={{
                trigger: "Colunas",
                panelTitle: "Colunas das oportunidades",
                reset: "Restaurar padrão",
                hint: CM_HELP.analytics.opportunitiesColumns,
                columnAriaLabel: (label) => `Exibir coluna ${label}`,
                reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
              }}
            />
          </>
        }
      />
      <CommercialDataTable
        rows={rows}
        columns={columns}
        rowKey={(row) => `${row.branch}-${row.proposal_number}-${row.revision}`}
        layout="section"
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSortChange={onSortChange}
        enableColumnReorder
        onColumnOrderChange={applyVisibleOrder}
        onRowClick={
          onRowClick ??
          ((row) =>
            navigateAnalyticsOpportunityDetail(row.proposal_number, {
              basePath,
              search: detailSearch,
            }))
        }
        rowClickRole="button"
      />
    </div>
  );
}
