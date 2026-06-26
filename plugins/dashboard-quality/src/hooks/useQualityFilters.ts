import { useCallback, useEffect, useState } from "react";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
  inputDateToApi,
} from "../utils/dates";
import { resolveApiBranch } from "../utils/branchClientFilters";
import {
  readQualityFilters,
  writeFiltersToUrl,
  type QualityFilterUrlState,
} from "../utils/filterUrl";
import type { DateRangeParams } from "../types/ppm";

export function useQualityFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readQualityFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(() => readQualityFilters().dateEnd);
  const [branches, setBranchesState] = useState(
    () => readQualityFilters().branches
  );

  const syncToUrl = useCallback((state: QualityFilterUrlState) => {
    writeFiltersToUrl(state);
  }, []);

  useEffect(() => {
    syncToUrl({ dateStart, dateEnd, branches });
  }, [dateStart, dateEnd, branches, syncToUrl]);

  useEffect(() => {
    const onPopState = () => {
      const next = readQualityFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const setDateStart = useCallback((value: string) => {
    setDateStartState(value);
  }, []);

  const setDateEnd = useCallback((value: string) => {
    setDateEndState(value);
  }, []);

  const setBranches = useCallback((value: string[]) => {
    setBranchesState(value);
  }, []);

  const apiParams: DateRangeParams = {
    branch: resolveApiBranch(branches),
    date_start: inputDateToApi(dateStart),
    date_end: inputDateToApi(dateEnd),
  };

  const filterState: QualityFilterUrlState = {
    dateStart,
    dateEnd,
    branches,
  };

  const resetFilters = useCallback(() => {
    const next = {
      dateStart: getFirstDayOfMonthInputValue(),
      dateEnd: getTodayInputValue(),
      branches: [] as string[],
    };

    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
    setBranchesState(next.branches);
    writeFiltersToUrl(next);
  }, []);

  return {
    dateStart,
    dateEnd,
    branches,
    setDateStart,
    setDateEnd,
    setBranches,
    apiParams,
    filterState,
    resetFilters,
  };
}
