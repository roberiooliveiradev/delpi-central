import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField } = createDashboardFiltersKit({
  prefix: "dh",
  labels: { filtersAriaLabel: "Filtros do dashboard de RH" },
});
