import { useCallback, useEffect, useState } from "react";
import type { ProductionFilterParams } from "../types/production";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readProductionFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type ProductionFilterUrlState,
} from "../utils/filterUrl";

export function useProductionFilters() {
  const initial = readProductionFilters();
  const {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceAll,
  } = useCompetenceLinkedDates(initial);
  const [branches, setBranchesState] = useState(initial.branches);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches });
  }, [dateStart, dateEnd, competence, branches]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readProductionFilters();
      replaceAll(next);
      setBranchesState(next.branches);
    });
  }, [replaceAll]);

  const apiParams: ProductionFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: ProductionFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    apiParams,
    filterState,
  };
}
