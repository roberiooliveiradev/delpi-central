import {
  FilterInputField as PluginFilterInputField,
  FiltersRow as PluginFiltersRow,
  createFilterBarShell,
  filtersRowBemClasses,
  type FilterInputFieldProps,
  type FiltersRowProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("ip");

export const FilterBarShell = createFilterBarShell({
  prefix: "ip",
  defaultAriaLabel: "Filtro de período",
});

export function FiltersRow(
  props: Omit<FiltersRowProps, "classNames">,
) {
  return <PluginFiltersRow classNames={FIELD_CLASS_NAMES} compact {...props} />;
}

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}
