import {
  createDashboardNativeFormFields,
  createFilterBarShell,
  formFieldShellBemClasses,
} from "@delpi/plugin-ui/index";

export const { TextField: FiTextField } = createDashboardNativeFormFields({
  classNames: formFieldShellBemClasses("fi"),
});

export const FilterBarShell = createFilterBarShell({
  prefix: "fi",
  withGrid: true,
  defaultAriaLabel: "Filtros de período",
});
