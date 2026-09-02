import {
  createDashboardFiltersKit,
  filterToolbarRowBemClasses,
  filtersRowBemClasses,
  FilterInputField as PluginFilterInputField,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const PREFIX = "pp";

const filtersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros do painel" },
  portalScopeClassName: "dashboard-production-pulse",
});

export const PpFiltersRow = filtersKit.FiltersRow;
export const PpFilterSelectField = filtersKit.FilterSelectField;
export const PpFilterToolbarRowClasses = filterToolbarRowBemClasses(PREFIX);

const fieldClassNames = filtersRowBemClasses(PREFIX);

export function PpFilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={fieldClassNames} {...props} />;
}
