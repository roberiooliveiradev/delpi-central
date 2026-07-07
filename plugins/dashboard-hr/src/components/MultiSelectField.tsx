import {
  createDashboardMultiSelectField,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui";

const LABELS = {
  emptyLabel: "Todos",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionado(s)`,
} satisfies MultiSelectFieldLabels;

export const MultiSelectField = createDashboardMultiSelectField({ prefix: "dh", labels: LABELS });

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
