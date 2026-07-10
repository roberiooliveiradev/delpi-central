import {
  DataTable as BaseDataTable,
  dataTableBemClasses,
  type DataTableClassNames,
  type DataTableLabels,
} from "@delpi/plugin-ui/index";

import type { DataTableColumn } from "./types";
import "./DataTable.css";

const DM_TABLE_CLASS_NAMES: DataTableClassNames = {
  ...dataTableBemClasses("dm"),
  outerRoot: "dm-datatable",
  scrollWrap: "dm-datatable__scroll",
  wrapSection: "dm-datatable__scroll",
  wrapEmbedded: "dm-datatable__scroll",
  table: "dm-datatable__table",
  tableClickable: "dm-datatable__table dm-datatable__table--clickable",
  sortableColumn: "dm-datatable__col--sortable",
  empty: "dm-datatable__empty",
  emptyInnerWrapper: true,
  headerLabel: "dm-datatable__header-label",
  headerText: "dm-datatable__header-label",
  sortButton: "dm-datatable__sort-button",
  sortButtonActive: "dm-datatable__sort-button",
  sortIndicator: "dm-datatable__sort-indicator",
  rowClickable: "is-clickable",
};

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
} satisfies DataTableLabels;

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
  getRowKey: (row: T, index: number) => string;
  getRowClassName?: (row: T) => string | undefined;
  onRowClick?: (row: T) => void;
  sortKey?: string | null;
  sortDirection?: "asc" | "desc";
  onSortChange?: (columnKey: string) => void;
};

export function DataTable<T>({
  getRowKey,
  ...props
}: DataTableProps<T>) {
  return (
    <BaseDataTable
      layout="scroll"
      rowClickRole="button"
      rowKey={getRowKey}
      classNames={DM_TABLE_CLASS_NAMES}
      labels={LABELS}
      {...props}
    />
  );
}

export type { DataTableColumn };
