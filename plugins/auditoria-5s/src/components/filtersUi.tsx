import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "a5s-analytics-filter-field",
  fieldLabel: "a5s-analytics-filter-field__label",
};

export const FilterBarShell = createFilterBarShell({
  prefix: "a5s",
  block: "analytics-filters",
  withGrid: true,
  embeddedByDefault: true,
  defaultAriaLabel: "Filtros do painel de auditoria 5S",
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}

export function FilterSelectField(props: Omit<FilterSelectFieldProps, "classNames">) {
  return <PluginFilterSelectField classNames={FIELD_CLASS_NAMES} {...props} />;
}
