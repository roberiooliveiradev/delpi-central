import { useCallback, useEffect, useState } from "react";
import type { EngineeringFilterParams } from "../types/engineering";
import { inputDateToApi } from "../utils/dates";
import {
  readEngineeringFilters,
  writeFiltersToUrl,
  type EngineeringFilterUrlState,
} from "../utils/filterUrl";

export function useEngineeringFilters() {
  const [dateStart, setDateStartState] = useState(
    () => readEngineeringFilters().dateStart
  );
  const [dateEnd, setDateEndState] = useState(
    () => readEngineeringFilters().dateEnd
  );
  const [branch, setBranchState] = useState(() => readEngineeringFilters().branch);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch });
  }, [dateStart, dateEnd, branch]);

  useEffect(() => {
    const onPopState = () => {
      const next = readEngineeringFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: EngineeringFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    filial_id: branch || undefined,
    branch: branch || undefined,
  };

  const filterState: EngineeringFilterUrlState = {
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
