import {
  createDashboardSelectControl,
  selectControlBemClasses,
} from "@delpi/plugin-ui";

export type { SelectOption } from "@delpi/plugin-ui";

const LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => (label ? `Buscar ${label}` : "Buscar opções"),
};

export const SelectControl = createDashboardSelectControl({
  control: selectControlBemClasses("ds"),
  labels: LABELS,
});
