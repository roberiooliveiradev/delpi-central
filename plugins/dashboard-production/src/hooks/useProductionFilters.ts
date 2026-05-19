import { useCallback, useEffect, useState } from "react";
import type { ProductionFilterParams } from "../types/production";
import { inputDateToApi } from "../utils/dates";
import {
  readProductionFilters,
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
  const [branch, setBranchState] = useState(() => readProductionFilters().branch);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch]);

  useEffect(() => {
    const onPopState = () => {
      const next = readProductionFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: ProductionFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
  };

  const filterState: ProductionFilterUrlState = { dateStart, dateEnd, branch };

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
