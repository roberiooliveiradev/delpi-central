import { useCallback, useEffect, useState } from "react";
import type { SuppliesFilterParams } from "../types/supplies";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import {
  readSuppliesFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type SuppliesFilterUrlState,
} from "../utils/filterUrl";

export function useSuppliesFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readSuppliesFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(
    () => readSuppliesFilters().dateEnd
  );
  const [branches, setBranchesState] = useState(
    () => readSuppliesFilters().branches
  );
  const [location, setLocationState] = useState(
    () => readSuppliesFilters().location
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches, location });
  }, [dateStart, dateEnd, branches, location]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readSuppliesFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
      setLocationState(next.location);
    });
  }, []);

  const resolvedBranch = resolveApiBranch(branches);

  const periodParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const stockParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const filterState: SuppliesFilterUrlState = {
    dateStart,
    dateEnd,
    branches,
    location,
  };

  return {
    dateStart,
    dateEnd,
    branches,
    location,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setLocation: useCallback((v: string) => setLocationState(v), []),
    periodParams,
    stockParams,
    filterState,
  };
}
