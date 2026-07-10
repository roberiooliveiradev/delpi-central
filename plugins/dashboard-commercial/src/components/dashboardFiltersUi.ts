import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "dc",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
