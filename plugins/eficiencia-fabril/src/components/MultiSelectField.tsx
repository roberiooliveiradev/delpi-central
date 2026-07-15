import {
  createDashboardMultiSelectField,
  multiSelectBemClasses,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui/index";

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

/* FilterBarShell já é o card — root sem ef-filter-box para não aninhar cards. */
export const MultiSelectField = createDashboardMultiSelectField({
  labels: LABELS,
  classNames: {
    ...multiSelectBemClasses("ef"),
    root: "ef-field ef-field--multi-select",
  },
});
export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
