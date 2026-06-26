import { useCallback, useEffect, useState } from "react";
import type { EngineeringFilterParams } from "../types/engineering";
import { resolveApiBranch } from "../utils/branchClientFilters";
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
  const [branches, setBranchesState] = useState(
    () => readEngineeringFilters().branches
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches });
  }, [dateStart, dateEnd, branches]);

  useEffect(() => {
    const onPopState = () => {
      const next = readEngineeringFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const resolvedBranch = resolveApiBranch(branches);

  const apiParams: EngineeringFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    filial_id: resolvedBranch,
    branch: resolvedBranch,
  };

  const filterState: EngineeringFilterUrlState = {
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
