import type { ComponentProps } from "react";

import {
  DataTable as BaseDataTable,
  dataTableBemClasses,
  type DataTableColumn,
  type DataTableLabels,
} from "@delpi/plugin-ui/index";

const TABLE_CLASS_NAMES = dataTableBemClasses("pp");

const LABELS = {
  emptyMessage: "Nenhum dispositivo encontrado.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
} satisfies DataTableLabels;

export type { DataTableColumn };

type PpDataTableProps<T> = Omit<
  ComponentProps<typeof BaseDataTable<T>>,
  "classNames" | "labels"
>;

export function PpDataTable<T>(props: PpDataTableProps<T>) {
  return <BaseDataTable classNames={TABLE_CLASS_NAMES} labels={LABELS} {...props} />;
}
