import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "ds",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
