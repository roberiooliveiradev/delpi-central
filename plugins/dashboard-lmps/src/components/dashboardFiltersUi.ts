import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "lmps",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
