import {
  createDashboardMultiSelectField,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
  multiSelectBemClasses,
} from "@delpi/plugin-ui";

const LABELS = {
  emptyLabel: "Todos os clientes",
  searchPlaceholder: "Buscar cliente…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar seleção",
  emptyOptions: "Nenhum cliente encontrado.",
  multipleSelected: (count: number) => `${count} clientes selecionados`,
} satisfies MultiSelectFieldLabels;

const base = multiSelectBemClasses("pva");

export const MultiSelectField = createDashboardMultiSelectField({
  labels: LABELS,
  classNames: {
    ...base,
    root: "pva-field pva-field--clients",
    actionButton: "pva-btn pva-btn--ghost pva-btn--sm",
  },
});

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
