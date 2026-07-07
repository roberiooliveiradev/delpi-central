import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "dp",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
