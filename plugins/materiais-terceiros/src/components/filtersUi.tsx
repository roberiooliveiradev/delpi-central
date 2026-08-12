import {
  FilterInputField as PluginFilterInputField,
  createDashboardFilterCheckboxField,
  createDashboardFiltersKit,
  createFilterBarShell,
  filterCheckboxFieldBemClasses,
  filtersRowBemClasses,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("mt");

export const FilterBarShell = createFilterBarShell({
  prefix: "mt",
  defaultAriaLabel: "Filtros de materiais de terceiros",
});

const filtersKit = createDashboardFiltersKit({
  prefix: "mt",
  labels: { filtersAriaLabel: "Filtros de materiais de terceiros" },
  portalScopeClassName: "dashboard-materiais-terceiros",
});

export const FilterSelectField = filtersKit.FilterSelectField;
export const FilterCheckboxField = createDashboardFilterCheckboxField({
  classNames: filterCheckboxFieldBemClasses("mt"),
  labels: { defaultCheckboxLabel: "Ativar" },
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}
