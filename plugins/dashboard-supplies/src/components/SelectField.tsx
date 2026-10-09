import {
  createDashboardSelectField,
  selectFieldPacClasses,
} from "@delpi/plugin-ui/index";

export type { SelectOption } from "@delpi/plugin-ui/index";

const CONTROL_LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => `Buscar ${label ?? "opções"}`,
};

export const SelectField = createDashboardSelectField({
  ...selectFieldPacClasses("ds"),
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "Todos",
    control: CONTROL_LABELS,
  },
});
