import {
  DataTable as BaseDataTable,
  dataTableBemClasses,
  type DataTableClassNames,
  type DataTableLabels,
} from "@delpi/plugin-ui/index";

import type { DataTableColumn } from "./types";
import "./DataTable.css";

const kit = dataTableBemClasses("dm");

/** Kit canônico + outer/scroll de domínio (cards mobile / escopo CSS). */
const DM_TABLE_CLASS_NAMES: DataTableClassNames = {
  ...kit,
  outerRoot: "dm-datatable",
  scrollWrap: "dm-datatable__scroll dm-table-wrap delpi-ui-table-wrap",
  sortableColumn: "dm-table__col--sortable delpi-ui-table__col--sortable",
  rowClickable: `${kit.rowClickable} is-clickable`,
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
