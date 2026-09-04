import { runTabularExport, type DataTableColumn } from "@delpi/plugin-ui/index";
import { useMemo, useState } from "react";

import type { OpportunityCollaboratorSummaryRow } from "../../../api/analyticsApi";
import {
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialTableColumnVisibilityMenu,
  CommercialTableFontSizeControls,
  CommercialTabularExportButtons,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  nextTableSortState,
  sortTableRows,
  type TableSortDirection,
} from "../../../utils/sortTableRows";
import { useOpportunitiesTablePreferences } from "../hooks/useOpportunitiesTablePreferences";
import {
  OPPORTUNITY_COLLABORATOR_COLUMN_CATALOG,
  OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY,
  OPPORTUNITY_COLLABORATOR_EMPTY_FALLBACK_KEYS,
  OPPORTUNITY_COLLABORATOR_FONT_STORAGE_KEY,
} from "../utils/opportunityTableColumns";

type OpportunityCollaboratorSummaryTableProps = {
  rows: OpportunityCollaboratorSummaryRow[];
  loading?: boolean;
  onSellerClick?: (sellerCode: string) => void;
};

function buildColumns(): DataTableColumn<OpportunityCollaboratorSummaryRow>[] {
  return [
    {
      key: "seller",
      header: "Vendedor",
      sortable: true,
      sortValue: (row) => row.sellerName || row.sellerCode || "",
      render: (row) => row.sellerName || row.sellerCode || "—",
    },
    {
      key: "open",
      header: "Abertas",
      sortable: true,
      sortValue: (row) => row.openCount,
      align: "right",
      render: (row) => String(row.openCount),
    },
    {
      key: "won",
      header: "Ganhas",
      sortable: true,
      sortValue: (row) => row.wonCount,
      align: "right",
      render: (row) => String(row.wonCount),
    },
    {
      key: "lost",
      header: "Perdidas",
      sortable: true,
      sortValue: (row) => row.lostCount,
      align: "right",
      render: (row) => String(row.lostCount),
    },
    {
      key: "total",
      header: "Total",
      sortable: true,
      sortValue: (row) => row.totalCount,
      align: "right",
      render: (row) => String(row.totalCount),
    },
    {
      key: "age",
      header: "Idade média (dias)",
      sortable: true,
      sortValue: (row) => row.ageDaysAvg ?? -1,
      align: "right",
      render: (row) =>
        row.ageDaysAvg == null ? "—" : row.ageDaysAvg.toLocaleString("pt-BR"),
    },
  ];
}

export function OpportunityCollaboratorSummaryTable({
  rows,
  loading = false,
  onSellerClick,
}: OpportunityCollaboratorSummaryTableProps) {
  const [sortKey, setSortKey] = useState("total");
  const [sortDirection, setSortDirection] = useState<TableSortDirection>("desc");

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
    columnsStorageKey: OPPORTUNITY_COLLABORATOR_COLUMNS_STORAGE_KEY,
    fontSizeStorageKey: OPPORTUNITY_COLLABORATOR_FONT_STORAGE_KEY,
    columns: OPPORTUNITY_COLLABORATOR_COLUMN_CATALOG,
    emptyFallbackKeys: [...OPPORTUNITY_COLLABORATOR_EMPTY_FALLBACK_KEYS],
  });

  const baseColumns = useMemo(() => buildColumns(), []);
  const columns = useMemo(
    () => filterColumns(baseColumns),
    [baseColumns, filterColumns],
  );
  const sortedRows = useMemo(
    () => sortTableRows(rows, baseColumns, sortKey, sortDirection),
    [rows, baseColumns, sortKey, sortDirection],
  );

  if (loading) {
    return <CommercialLoadingCard title="Carregando…" variant="panel" />;
  }

  if (!rows.length) {
    return (
      <CommercialEmptyState defaultMessage="Nenhum colaborador com oportunidades no período." />
    );
  }

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
                    title: "Oportunidades por colaborador",
                    columns: OPPORTUNITY_COLLABORATOR_COLUMN_CATALOG.map((column) => ({
                      key: column.key,
                      label: column.label,
                    })),
                    rows: sortedRows.map((row) => ({
                      seller: row.sellerName || row.sellerCode || "",
                      open: row.openCount,
                      won: row.wonCount,
                      lost: row.lostCount,
                      total: row.totalCount,
                      age:
                        row.ageDaysAvg == null
                          ? ""
                          : row.ageDaysAvg.toLocaleString("pt-BR"),
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
                panelTitle: "Colunas por colaborador",
                reset: "Restaurar padrão",
                hint: CM_HELP.analytics.collaboratorColumns,
                columnAriaLabel: (label) => `Exibir coluna ${label}`,
                reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
              }}
            />
          </>
        }
      />
      <CommercialDataTable
        rows={sortedRows}
        columns={columns}
        rowKey={(row) => row.sellerCode || "_"}
        layout="section"
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSortChange={(columnKey) => {
          const next = nextTableSortState(sortKey, sortDirection, columnKey);
          setSortKey(next.sortKey);
          setSortDirection(next.sortDirection);
        }}
        enableColumnReorder
        onColumnOrderChange={applyVisibleOrder}
        onRowClick={
          onSellerClick
            ? (row) => {
                const code = (row.sellerCode || "").trim();
                if (code) onSellerClick(code);
              }
            : undefined
        }
        rowClickRole={onSellerClick ? "button" : undefined}
      />
    </div>
  );
}
