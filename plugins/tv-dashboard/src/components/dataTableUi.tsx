import {
  DataTable as PluginDataTable,
  dataTableBemClasses,
  type DashboardDataTableProps,
  type DataTableColumn,
  type DataTableLabels,
} from "@delpi/plugin-ui/index";

const CLASS_NAMES = dataTableBemClasses("td");

const LABELS = {
  emptyMessage: "Nenhuma programação cadastrada.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
} satisfies DataTableLabels;

export function DataTable<T>(props: DashboardDataTableProps<T>) {
  return <PluginDataTable classNames={CLASS_NAMES} labels={LABELS} {...props} />;
}

export type { DataTableColumn };
