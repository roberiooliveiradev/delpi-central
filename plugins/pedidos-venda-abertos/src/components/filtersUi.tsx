import {
  FilterInputField as PluginFilterInputField,
  createDashboardFiltersKit,
  createFilterBarShell,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "pva-field",
  fieldLabel: "pva-field__label",
};

const WIDE_FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "pva-field pva-field--wide",
  fieldLabel: "pva-field__label",
};

export const FilterBarShell = createFilterBarShell({
  prefix: "pva",
  withGrid: true,
  defaultAriaLabel: "Filtros",
});

const {
  FilterSelectField: KitFilterSelectField,
} = createDashboardFiltersKit({
  prefix: "pva",
  labels: { filtersAriaLabel: "Filtros" },
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

export const FilterSelectField = KitFilterSelectField;
