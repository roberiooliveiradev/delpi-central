import {
  DataTable as BaseDataTable,
  dataTableBemClasses,
  type DashboardDataTableProps,
} from "@delpi/plugin-ui";

export type { DataTableColumn } from "@delpi/plugin-ui";

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

const classNames = dataTableBemClasses("lmps");

export function DataTable<T>(props: DashboardDataTableProps<T>) {
  return <BaseDataTable classNames={classNames} labels={LABELS} {...props} />;
}
