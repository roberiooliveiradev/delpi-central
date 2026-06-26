import { useCallback, useEffect, useState } from "react";
import type { FinancialFilterParams } from "../types/financial";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import {
  readFinancialFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type FinancialFilterUrlState,
} from "../utils/filterUrl";

export function useFinancialFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readFinancialFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(
    () => readFinancialFilters().dateEnd
  );
  const [branches, setBranchesState] = useState(
    () => readFinancialFilters().branches
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches });
  }, [dateStart, dateEnd, branches]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readFinancialFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
    });
  }, []);

  const apiParams: FinancialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: FinancialFilterUrlState = {
    dateStart,
    dateEnd,
    branches,
  };

  return {
    dateStart,
    dateEnd,
    branches,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    apiParams,
    filterState,
  };
}
