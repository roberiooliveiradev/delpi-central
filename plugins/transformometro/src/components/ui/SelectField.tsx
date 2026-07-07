import {
  createDashboardSelectField,
  selectFieldTransformometroClasses,
} from "@delpi/plugin-ui";

export type { SelectOption } from "@delpi/plugin-ui";

const CONTROL_LABELS = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (label?: string) => (label ? `Buscar ${label}` : "Buscar opções"),
};

export const SelectField = createDashboardSelectField({
  ...selectFieldTransformometroClasses("ds"),
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "—",
    control: CONTROL_LABELS,
  },
});
