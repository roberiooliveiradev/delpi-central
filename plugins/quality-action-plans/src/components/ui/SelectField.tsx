import {
  createDashboardSelectField,
  selectFieldPacClasses,
} from "@delpi/plugin-ui";

export type { SelectOption } from "@delpi/plugin-ui";

const CONTROL_LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => `Buscar ${label ?? "opções"}`,
};

export const SelectField = createDashboardSelectField({
  ...selectFieldPacClasses("pac"),
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "—",
    control: CONTROL_LABELS,
  },
});
