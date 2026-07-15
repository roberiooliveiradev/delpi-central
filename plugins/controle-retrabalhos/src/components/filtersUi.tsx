import {
  FilterInputField as PluginFilterInputField,
  createFilterBarShell,
  filtersRowBemClasses,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("cr");

export const FilterBarShell = createFilterBarShell({
  prefix: "cr",
  defaultAriaLabel: "Filtros de período",
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}
