import {
  FilterInputField as PluginFilterInputField,
  createFilterBarShell,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "cr-field",
  fieldLabel: "cr-field__label",
};

export const FilterBarShell = createFilterBarShell({
  prefix: "cr",
  defaultAriaLabel: "Filtros de período",
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}
