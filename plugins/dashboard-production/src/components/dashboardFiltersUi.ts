import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "dp",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
