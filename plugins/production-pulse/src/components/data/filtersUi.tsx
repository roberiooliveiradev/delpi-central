import {
  createDashboardFiltersKit,
  createFilterBarShell,
  filtersRowBemClasses,
  FilterInputField as PluginFilterInputField,
  type FilterInputFieldProps,
} from "@delpi/plugin-ui/index";

const PREFIX = "pp";

export const PpFilterBarShell = createFilterBarShell({
  prefix: PREFIX,
  withGrid: true,
  defaultAriaLabel: "Filtros do painel",
});

const filtersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros do painel" },
  portalScopeClassName: "dashboard-production-pulse",
});

export const PpFilterSelectField = filtersKit.FilterSelectField;

const fieldClassNames = filtersRowBemClasses(PREFIX);

export function PpFilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={fieldClassNames} {...props} />;
}
