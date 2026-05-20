import { useCallback, useEffect, useState } from "react";
import type { HrFilterParams } from "../types/hr";
import { inputDateToApi } from "../utils/dates";
import {
  readHrFilters,
  writeFiltersToUrl,
  type HrFilterUrlState,
} from "../utils/filterUrl";

export function useHrFilters() {
  const [dateStart, setDateStartState] = useState(() => readHrFilters().dateStart);
  const [dateEnd, setDateEndState] = useState(() => readHrFilters().dateEnd);
  const [branch, setBranchState] = useState(() => readHrFilters().branch);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch]);

  useEffect(() => {
    const onPopState = () => {
      const next = readHrFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: HrFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
  };

  const filterState: HrFilterUrlState = { dateStart, dateEnd, branch };

  return {
    dateStart,
    dateEnd,
    branch,
    setDateStart: useCallback((value: string) => setDateStartState(value), []),
    setDateEnd: useCallback((value: string) => setDateEndState(value), []),
    setBranch: useCallback((value: string) => setBranchState(value), []),
    apiParams,
    filterState,
  };
}
