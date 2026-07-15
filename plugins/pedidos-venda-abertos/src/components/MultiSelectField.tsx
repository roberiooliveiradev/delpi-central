import {
  createDashboardMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui/index";

const LABELS = {
  emptyLabel: "Todos os clientes",
  searchPlaceholder: "Buscar cliente…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar seleção",
  emptyOptions: "Nenhum cliente encontrado.",
  multipleSelected: (count: number) => `${count} clientes selecionados`,
} satisfies MultiSelectFieldLabels;

/* FilterBar já estruturado — root sem pva-filter-box para não aninhar cards. */
export const MultiSelectField = createDashboardMultiSelectField({
  labels: LABELS,
  classNames: {
    ...multiSelectBemClasses("pva"),
    root: "pva-field pva-field--clients",
  },
});

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
