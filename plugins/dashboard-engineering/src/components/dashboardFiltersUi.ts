import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "ds",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
