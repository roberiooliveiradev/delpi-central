import { useCallback, useEffect, useState } from "react";
import type { SuppliesFilterParams } from "../types/supplies";
import { inputDateToApi } from "../utils/dates";
import {
  readSuppliesFilters,
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
  const [branch, setBranchState] = useState(() => readSuppliesFilters().branch);
  const [location, setLocationState] = useState(
    () => readSuppliesFilters().location
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch, location });
  }, [dateStart, dateEnd, branch, location]);

  useEffect(() => {
    const onPopState = () => {
      const next = readSuppliesFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
      setLocationState(next.location);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const periodParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
    location: location || undefined,
  };

  const stockParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
    location: location || undefined,
  };

  const filterState: SuppliesFilterUrlState = {
    dateStart,
    dateEnd,
    branch,
    location,
  };

  return {
    dateStart,
    dateEnd,
    branch,
    location,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
    setBranch: useCallback((v: string) => setBranchState(v), []),
    setLocation: useCallback((v: string) => setLocationState(v), []),
    periodParams,
    stockParams,
    filterState,
  };
}
