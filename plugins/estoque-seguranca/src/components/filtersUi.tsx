import {
  FilterInputField as PluginFilterInputField,
  createDashboardFilterCheckboxField,
  createDashboardFiltersKit,
  createFilterBarShell,
  filterCheckboxFieldBemClasses,
  filtersRowBemClasses,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("ess");

export const FilterBarShell = createFilterBarShell({
  prefix: "ess",
  defaultAriaLabel: "Filtros de estoque de segurança",
});

const filtersKit = createDashboardFiltersKit({
  prefix: "ess",
  labels: { filtersAriaLabel: "Filtros de estoque de segurança" },
  portalScopeClassName: "dashboard-estoque-seguranca",
});

export const FilterSelectField = filtersKit.FilterSelectField;
export const FilterCheckboxField = createDashboardFilterCheckboxField({
  classNames: filterCheckboxFieldBemClasses("ess"),
  labels: { defaultCheckboxLabel: "Ativar" },
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}
