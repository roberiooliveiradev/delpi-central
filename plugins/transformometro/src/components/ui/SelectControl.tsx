import { createDashboardSelectControl, selectControlBemClasses } from "@delpi/plugin-ui/index";
const LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => (label ? `Buscar ${label}` : "Buscar opções"),
};

export const SelectControl = createDashboardSelectControl({
  control: selectControlBemClasses("ds"),
  labels: LABELS,
});
