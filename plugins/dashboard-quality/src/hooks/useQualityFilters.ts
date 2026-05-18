import { useCallback, useEffect, useState } from "react";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
  inputDateToApi,
} from "../utils/dates";
import {
  readFiltersFromUrl,
  writeFiltersToUrl,
  type QualityFilterUrlState,
} from "../utils/filterUrl";
import type { DateRangeParams } from "../types/ppm";

export function useQualityFilters() {
  const [dateStart, setDateStartState] = useState(() =>
    readFiltersFromUrl().dateStart
  );
  const [dateEnd, setDateEndState] = useState(() => readFiltersFromUrl().dateEnd);
  const [branch, setBranchState] = useState(() => readFiltersFromUrl().branch);

  const syncToUrl = useCallback((state: QualityFilterUrlState) => {
    writeFiltersToUrl(state);
  }, []);

  useEffect(() => {
    syncToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch, syncToUrl]);

  useEffect(() => {
    const onPopState = () => {
      const fromUrl = readFiltersFromUrl();
      setDateStartState(fromUrl.dateStart);
      setDateEndState(fromUrl.dateEnd);
      setBranchState(fromUrl.branch);
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

  const setBranch = useCallback((value: string) => {
    setBranchState(value);
  }, []);

  const apiParams: DateRangeParams = {
    branch: branch || undefined,
    date_start: inputDateToApi(dateStart),
    date_end: inputDateToApi(dateEnd),
  };

  const filterState: QualityFilterUrlState = {
    dateStart,
    dateEnd,
    branch,
  };

  const resetFilters = useCallback(() => {
    const next = {
      dateStart: getFirstDayOfMonthInputValue(),
      dateEnd: getTodayInputValue(),
      branch: "",
    };

    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
    setBranchState(next.branch);
    writeFiltersToUrl(next);
  }, []);

  return {
    dateStart,
    dateEnd,
    branch,
    setDateStart,
    setDateEnd,
    setBranch,
    apiParams,
    filterState,
    resetFilters,
  };
}
