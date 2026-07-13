import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "kz",
  portalScopeClassName: "dashboard-cadastro-kaizen",
  labels: {
    filtersAriaLabel: "Filtros de kaizen",
  },
});
