import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "kz",
  portalScopeClassName: "dashboard-kaizometro",
  labels: {
    filtersAriaLabel: "Filtros de kaizen",
  },
});
