import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "dq",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
