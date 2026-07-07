import { createDashboardFiltersKit } from "@delpi/plugin-ui";

export const { FiltersRow, FilterInputField, FilterSelectField } = createDashboardFiltersKit({
  prefix: "kz",
  labels: {
    filtersAriaLabel: "Filtros de kaizen",
  },
});
