import {
  DataTable as BaseDataTable,
  dataTableBemClasses,
  type DataTableColumn as KitDataTableColumn,
  type DataTableLabels,
} from "@delpi/plugin-ui/index";
import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyText?: string;
  getRowKey: (row: T, index: number) => string;
};

const SI_TABLE_CLASS_NAMES = dataTableBemClasses("si");

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
} satisfies DataTableLabels;

/** Thin wrapper — chrome da tabela no kit (`delpi-ui-table*`). */
export function DataTable<T>({
  columns,
  rows,
  loading = false,
  emptyText,
  getRowKey,
}: DataTableProps<T>) {
  const kitColumns: KitDataTableColumn<T>[] = columns.map((column) => ({
    key: column.key,
    header: column.header,
    render: (row) => (column.render ? column.render(row) : "-"),
  }));

  return (
    <BaseDataTable
      columns={kitColumns}
      rows={rows}
      loading={loading}
      emptyMessage={emptyText}
      rowKey={getRowKey}
      layout="section"
      classNames={SI_TABLE_CLASS_NAMES}
      labels={LABELS}
    />
  );
}
