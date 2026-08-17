import {
  DataTable as PluginDataTable,
  dataTableBemClasses,
  type DashboardDataTableProps,
} from "@delpi/plugin-ui/index";

export const IE_TABLE = dataTableBemClasses("ie");

const LABELS = {
  emptyMessage: "Nenhum registro encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export function DataTable<T>(props: DashboardDataTableProps<T>) {
  return <PluginDataTable classNames={IE_TABLE} labels={LABELS} {...props} />;
}

export type { DataTableColumn } from "@delpi/plugin-ui/index";
