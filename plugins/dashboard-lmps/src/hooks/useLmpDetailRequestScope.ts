import { useMemo } from "react";

import { readLmpsFilters, resolveLmpsBranchFilter } from "../utils/filterUrl";

export type LmpDetailRequestScope = {
  dateStart: string;
  dateEnd: string;
  branch?: string;
};

export function useLmpDetailRequestScope(
  saleNumber: string,
  branch?: string,
): LmpDetailRequestScope {
  return useMemo(() => {
    const filters = readLmpsFilters();

    return {
      dateStart: filters.dateStart,
      dateEnd: filters.dateEnd,
      branch: branch ?? resolveLmpsBranchFilter(filters),
    };
  }, [saleNumber, branch]);
}
