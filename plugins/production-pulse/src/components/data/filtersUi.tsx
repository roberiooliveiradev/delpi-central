import {
  createDashboardFiltersKit,
  filterToolbarRowBemClasses,
  filtersRowBemClasses,
  FilterInputField as PluginFilterInputField,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui/index";

const PREFIX = "pp";

const filtersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros do painel" },
  portalScopeClassName: "dashboard-production-pulse",
});

export const PpFiltersRow = filtersKit.FiltersRow;
export const PpFilterToolbarRowClasses = filterToolbarRowBemClasses(PREFIX);

const BasePpFilterSelectField = filtersKit.FilterSelectField;

type PpFilterSelectFieldProps = Omit<
  FilterSelectFieldProps,
  "classNames" | "selectClassNames" | "selectLabels"
> & {
  searchable?: boolean;
};

/** Select de filtro com busca habilitada por padrão. */
export function PpFilterSelectField({ searchable = true, ...props }: PpFilterSelectFieldProps) {
  return <BasePpFilterSelectField searchable={searchable} {...props} />;
}

const fieldClassNames = filtersRowBemClasses(PREFIX);

export function PpFilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={fieldClassNames} {...props} />;
}
