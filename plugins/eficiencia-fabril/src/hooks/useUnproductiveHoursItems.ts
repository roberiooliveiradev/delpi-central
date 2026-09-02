import { useCallback, useMemo } from "react";

import { getUnproductiveHoursItems } from "../api/unproductiveHoursApi";
import type {
  UnproductiveHoursItemsFilters,
  UnproductiveHoursSort,
} from "../types/unproductiveHours";
import { UNPRODUCTIVE_HOURS_PAGE_SIZE } from "../types/unproductiveHours";
import { useAsyncResource } from "./useAsyncResource";

export function useUnproductiveHoursItems(
  filters: Omit<UnproductiveHoursItemsFilters, "page" | "page_size" | "sort"> | null,
  page: number,
  sort: UnproductiveHoursSort,
  enabled: boolean,
) {
  const filtersKey = useMemo(() => {
    if (!filters) return "";
    return [
      filters.branch,
      filters.start_date,
      filters.end_date,
      filters.stop_reason ?? "",
      filters.resource ?? "",
      filters.cost_center ?? "",
      filters.operator_code ?? "",
      page,
      sort,
    ].join("|");
  }, [filters, page, sort]);

  const fetcher = useCallback(
    async (signal: AbortSignal) => {
      if (!filters) {
        throw new Error("Filtros de horas improdutivas inválidos.");
      }
      return getUnproductiveHoursItems(
        {
          ...filters,
          page,
          page_size: UNPRODUCTIVE_HOURS_PAGE_SIZE,
          sort,
        },
        { signal },
      );
    },
    [filters, page, sort],
  );

  return useAsyncResource(fetcher, [filtersKey], enabled && Boolean(filters));
}
