import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "lmps",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
