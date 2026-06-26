import { useCallback, useEffect, useState } from "react";
import type { HrFilterParams } from "../types/hr";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import {
  readHrFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type HrFilterUrlState,
} from "../utils/filterUrl";

export function useHrFilters() {
  const [dateStart, setDateStartState] = useState(() => readHrFilters().dateStart);
  const [dateEnd, setDateEndState] = useState(() => readHrFilters().dateEnd);
  const [branches, setBranchesState] = useState(() => readHrFilters().branches);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches });
  }, [dateStart, dateEnd, branches]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readHrFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
    });
  }, []);

  const apiParams: HrFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: HrFilterUrlState = { dateStart, dateEnd, branches };

  return {
    dateStart,
    dateEnd,
    branches,
    setDateStart: useCallback((value: string) => setDateStartState(value), []),
    setDateEnd: useCallback((value: string) => setDateEndState(value), []),
    setBranches: useCallback((value: string[]) => setBranchesState(value), []),
    apiParams,
    filterState,
  };
}
