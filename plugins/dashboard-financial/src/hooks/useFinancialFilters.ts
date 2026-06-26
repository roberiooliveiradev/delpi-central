import { useCallback, useEffect, useState } from "react";
import type { FinancialFilterParams } from "../types/financial";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readFinancialFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type FinancialFilterUrlState,
} from "../utils/filterUrl";

export function useFinancialFilters() {
  const initial = readFinancialFilters();
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
      const next = readFinancialFilters();
      replaceAll(next);
      setBranchesState(next.branches);
    });
  }, [replaceAll]);

  const apiParams: FinancialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: FinancialFilterUrlState = {
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
