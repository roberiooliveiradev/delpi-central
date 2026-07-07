import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "dh",
  labels: { filtersAriaLabel: "Filtros do dashboard de RH" },
});
