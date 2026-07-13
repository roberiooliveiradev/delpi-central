import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "dq",
  portalScopeClassName: "dashboard-quality",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
