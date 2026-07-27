import {
  createHostContainedModalShell,
  confirmModalBemClasses,
  createDashboardFormActions,
  createDashboardFormGrid,
  createDashboardNativeFormFields,
  createDashboardSectionCard,
  createDashboardSelectField,
  createDashboardStatusBadge,
  createDashboardTextAreaField,
  createDashboardTextField,
  delpiUiClass,
  formActionsBemClasses,
  formFieldShellBemClasses,
  formGridBemClasses,
  sectionCardKaizenBemClasses,
  selectFieldPacClasses,
  textAreaFieldPacClasses,
  textFieldPacClasses,
} from "@delpi/plugin-ui/index";

export const LMPS_ROOT_CLASS = "dashboard-lmps";

export const HostContainedDialog = createHostContainedModalShell({
  prefix: "lmps",
  portalScopeClassName: LMPS_ROOT_CLASS,
  containedLayout: "dialog",
});

export const HostContainedFill = createHostContainedModalShell({
  prefix: "lmps",
  portalScopeClassName: LMPS_ROOT_CLASS,
  containedLayout: "fill",
});

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardKaizenBemClasses("lmps"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const FormActions = createDashboardFormActions({
  classNames: formActionsBemClasses("lmps"),
});

export const FormGrid = createDashboardFormGrid({
  classNames: formGridBemClasses("lmps"),
});

/** Campos de texto/área — dual-class `delpi-ui-filter-box` (kit). */
export const TextField = createDashboardTextField({
  classNames: textFieldPacClasses("lmps"),
});

export const TextAreaField = createDashboardTextAreaField({
  classNames: textAreaFieldPacClasses("lmps"),
});

const selectPac = selectFieldPacClasses("lmps");

/** Select canônico (SelectControl), não `<select>` nativo. */
export const SelectField = createDashboardSelectField({
  field: {
    ...selectPac.field,
    root: delpiUiClass("lmps-field", "delpi-ui-filter-box"),
  },
  control: selectPac.control,
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

/**
 * Somente tipos fora do TextField do kit (ex.: datetime-local).
 * Usa NativeTextField com `.delpi-ui-native-control`.
 */
export const {
  TextField: NativeTextField,
} = createDashboardNativeFormFields({
  classNames: {
    ...formFieldShellBemClasses("lmps"),
    root: delpiUiClass("lmps-field", "delpi-ui-filter-box"),
  },
});

export const StatusBadge = createDashboardStatusBadge({
  prefix: "lmps",
});

export const LMPS_CONFIRM_CLASSES = confirmModalBemClasses("lmps");
