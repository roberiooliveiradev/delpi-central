import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "dq",
  labels: { filtersAriaLabel: "Filtros do dashboard" },
});
