import {
  createDashboardSelectField,
  createDashboardSegmentToggle,
  createDashboardTextField,
  createDashboardDetailFieldGrid,
  selectFieldPacClasses,
  textFieldPacClasses,
} from "@delpi/plugin-ui/index";

export const TextField = createDashboardTextField({
  classNames: textFieldPacClasses("ii"),
});

const selectClasses = selectFieldPacClasses("ii");

export const SelectField = createDashboardSelectField({
  ...selectClasses,
  labels: {
    placeholder: "Selecione…",
    emptyLabel: "—",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});

export const SegmentToggle = createDashboardSegmentToggle("ii");

export const DetailFields = createDashboardDetailFieldGrid({
  prefix: "ii",
  labels: {
    fieldHelpAriaLabel: (label: string) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
  wrapLabels: true,
});
