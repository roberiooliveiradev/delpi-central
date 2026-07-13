import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "dc",
  portalScopeClassName: "dashboard-commercial",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
