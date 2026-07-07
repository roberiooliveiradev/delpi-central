import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "dc",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
