import {
  FilterInputField as PluginFilterInputField,
  createDashboardFiltersKit,
  createFilterBarShell,
  filtersRowBemClasses,
  withBemModifier,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("pva");

const WIDE_FIELD_CLASS_NAMES = {
  ...FIELD_CLASS_NAMES,
  filterBox: withBemModifier(FIELD_CLASS_NAMES.filterBox, "wide"),
};

export const FilterBarShell = createFilterBarShell({
  prefix: "pva",
  withGrid: true,
  defaultAriaLabel: "Filtros",
});

const { FilterSelectField: KitFilterSelectField } = createDashboardFiltersKit({
  prefix: "pva",
  portalScopeClassName: "dashboard-pedidos-venda-abertos",
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
