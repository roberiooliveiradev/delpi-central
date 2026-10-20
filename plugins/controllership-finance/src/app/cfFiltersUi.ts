/** Kit de filtros do Portal — `createDashboardFiltersKit` com prefixo `cf`. */
import { createDashboardFiltersKit } from "@delpi/plugin-ui/index";

import { CF_PORTAL_SCOPE } from "./controllershipFinanceUi";

export const { FiltersRow, FilterInputField, FilterSelectField } =
  createDashboardFiltersKit({
    prefix: "cf",
    labels: { filtersAriaLabel: "Filtros das baixas financeiras" },
    portalScopeClassName: CF_PORTAL_SCOPE,
  });
