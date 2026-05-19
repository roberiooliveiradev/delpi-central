import { useCallback, useEffect, useState } from "react";
import type { FinancialFilterParams } from "../types/financial";
import { inputDateToApi } from "../utils/dates";
import {
  readFinancialFilters,
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
  const [branch, setBranchState] = useState(() => readFinancialFilters().branch);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch]);

  useEffect(() => {
    const onPopState = () => {
      const next = readFinancialFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: FinancialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
  };

  const filterState: FinancialFilterUrlState = {
    dateStart,
    dateEnd,
    branch,
  };

  return {
    dateStart,
    dateEnd,
    branch,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
    setBranch: useCallback((v: string) => setBranchState(v), []),
    apiParams,
    filterState,
  };
}
