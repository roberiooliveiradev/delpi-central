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
  filterBox: "ie-field",
  fieldLabel: "ie-field__label",
};

const WIDE_FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "ie-field ie-field--wide",
  fieldLabel: "ie-field__label",
};

const SELECT_CLASS_NAMES = selectControlBemClasses("ie");

export const FilterBarShell = createFilterBarShell({
  prefix: "ie",
  withGrid: true,
  defaultAriaLabel: "Filtros do histórico",
});

type FieldExtras = { wide?: boolean };

export function FilterInputField({
  wide,
  ...props
}: Omit<FilterInputFieldProps, "classNames"> & FieldExtras) {
  return (
    <PluginFilterInputField
      classNames={wide ? WIDE_FIELD_CLASS_NAMES : FIELD_CLASS_NAMES}
      {...props}
    />
  );
}

export function FilterSelectField({
  wide,
  ...props
}: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels"> &
  FieldExtras) {
  return (
    <PluginFilterSelectField
      classNames={wide ? WIDE_FIELD_CLASS_NAMES : FIELD_CLASS_NAMES}
      selectClassNames={SELECT_CLASS_NAMES}
      {...props}
    />
  );
}
