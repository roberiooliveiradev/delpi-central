import { useCallback, useEffect, useState } from "react";
import { inputDateToApi } from "../utils/dates";
import {
  readCommercialFilters,
  writeFiltersToUrl,
  type CommercialFilterUrlState,
} from "../utils/filterUrl";
import type { CommercialFilterParams } from "../types/commercial";

export function useCommercialFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readCommercialFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(
    () => readCommercialFilters().dateEnd
  );
  const [branch, setBranchState] = useState(() => readCommercialFilters().branch);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch]);

  useEffect(() => {
    const onPopState = () => {
      const next = readCommercialFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: CommercialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
  };

  const filterState: CommercialFilterUrlState = { dateStart, dateEnd, branch };

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
