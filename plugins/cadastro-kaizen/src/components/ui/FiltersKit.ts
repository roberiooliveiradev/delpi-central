import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "kz",
  labels: {
    filtersAriaLabel: "Filtros de kaizen",
  },
});
