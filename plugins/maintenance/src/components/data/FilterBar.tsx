import { createFilterBarShell } from "@delpi/plugin-ui/index";

export const FilterBar = createFilterBarShell({
  prefix: "dm",
  withGrid: true,
  defaultAriaLabel: "Filtros",
});
