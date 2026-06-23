import { useMemo } from "react";

import { resolveCommercialApiBranch } from "../utils/commercialClientFilters";
import { readCommercialFilters } from "../utils/filterUrl";

export type CommercialDetailRequestScope = {
  dateStart: string;
  dateEnd: string;
  branch?: string;
  revision?: string;
};

export function useCommercialDetailRequestScope(
  proposalNumber: string,
  branch?: string,
  revision?: string
): CommercialDetailRequestScope {
  return useMemo(() => {
    const filters = readCommercialFilters();
    return {
      dateStart: filters.dateStart,
      dateEnd: filters.dateEnd,
      branch: branch ?? resolveCommercialApiBranch(filters.branches),
      revision: revision || undefined,
    };
  }, [proposalNumber, branch, revision]);
}
