import {
  FilterInputField as PluginFilterInputField,
  createDashboardFiltersKit,
  createFilterBarShell,
  filtersRowBemClasses,
  withBemModifier,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("cm");

const WIDE_FIELD_CLASS_NAMES = {
  ...FIELD_CLASS_NAMES,
  filterBox: withBemModifier(FIELD_CLASS_NAMES.filterBox, "wide"),
};

export const FilterBarShell = createFilterBarShell({
  prefix: "cm",
  withGrid: true,
  defaultAriaLabel: "Filtros",
});

const { FilterSelectField: KitFilterSelectField } = createDashboardFiltersKit({
  prefix: "cm",
  portalScopeClassName: "dashboard-commercial",
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
