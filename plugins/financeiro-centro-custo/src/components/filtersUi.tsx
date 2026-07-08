import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  selectControlBemClasses,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "fcc-field",
  fieldLabel: "fcc-field__label",
};

const SELECT_CLASS_NAMES = selectControlBemClasses("fcc");

export const FilterBarShell = createFilterBarShell({
  prefix: "fcc",
  defaultAriaLabel: "Filtros",
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}

export function FilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={FIELD_CLASS_NAMES}
      selectClassNames={SELECT_CLASS_NAMES}
      {...props}
    />
  );
}
