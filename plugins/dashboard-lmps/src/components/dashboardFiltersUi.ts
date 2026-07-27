import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

export const { FiltersRow, FilterInputField, FilterSelectField } =
  createDashboardFiltersKit({
    prefix: "lmps",
    labels: { filtersAriaLabel: "Filtros do dashboard" },
    portalScopeClassName: "dashboard-lmps",
  });
