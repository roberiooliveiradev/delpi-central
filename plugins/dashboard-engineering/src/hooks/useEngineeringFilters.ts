import { useCallback, useEffect, useState } from "react";
import type { EngineeringFilterParams } from "../types/engineering";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readEngineeringFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type EngineeringFilterUrlState,
} from "../utils/filterUrl";

export function useEngineeringFilters() {
  const initial = readEngineeringFilters();
  const {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceAll,
  } = useCompetenceLinkedDates(initial);
  const [branches, setBranchesState] = useState(initial.branches);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches });
  }, [dateStart, dateEnd, competence, branches]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readEngineeringFilters();
      replaceAll(next);
      setBranchesState(next.branches);
    });
  }, [replaceAll]);

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
    competence,
    branches,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    apiParams,
    filterState,
  };
}
