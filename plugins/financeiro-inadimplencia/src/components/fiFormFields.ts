import {
  createDashboardFilterCheckboxField,
  createDashboardNativeFormFields,
  createFilterBarShell,
  filterCheckboxFieldBemClasses,
  formFieldShellBemClasses,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = formFieldShellBemClasses("fi");

export const {
  TextField: FiTextField,
  SelectField: FiSelectField,
} = createDashboardNativeFormFields({
  classNames: FIELD_CLASS_NAMES,
});

export const FilterBarShell = createFilterBarShell({
  prefix: "fi",
  withGrid: true,
  defaultAriaLabel: "Filtros de período",
});

export const FilterCheckboxField = createDashboardFilterCheckboxField({
  classNames: filterCheckboxFieldBemClasses("fi"),
  labels: { defaultCheckboxLabel: "Ativar" },
});
