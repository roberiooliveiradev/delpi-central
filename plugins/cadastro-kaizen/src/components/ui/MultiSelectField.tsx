import {
  createDashboardMultiSelectField,
  type DashboardMultiSelectFieldProps,
  type MultiSelectFieldLabels,
  type MultiSelectOption,
} from "@delpi/plugin-ui";

const LABELS = {
  emptyLabel: "Todas",
  searchPlaceholder: "Buscar…",
  selectVisible: "Marcar visíveis",
  clear: "Limpar",
  emptyOptions: "Nenhuma opção encontrada.",
  multipleSelected: (count: number) => `${count} selecionada(s)`,
} satisfies MultiSelectFieldLabels;

export const MultiSelectField = createDashboardMultiSelectField({ prefix: "kz", labels: LABELS });

export type { MultiSelectOption };
export type MultiSelectFieldProps = DashboardMultiSelectFieldProps;
