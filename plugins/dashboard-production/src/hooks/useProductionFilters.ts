import { useCallback, useEffect, useState } from "react";
import type { ProductionFilterParams } from "../types/production";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import {
  readProductionFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type ProductionFilterUrlState,
} from "../utils/filterUrl";

export function useProductionFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readProductionFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(
    () => readProductionFilters().dateEnd
  );
  const [branches, setBranchesState] = useState(
    () => readProductionFilters().branches
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches });
  }, [dateStart, dateEnd, branches]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readProductionFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
    });
  }, []);

  const apiParams: ProductionFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: ProductionFilterUrlState = {
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
