import { useCallback, useEffect, useState } from "react";
import type { HrFilterParams } from "../types/hr";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readHrFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type HrFilterUrlState,
} from "../utils/filterUrl";

export function useHrFilters() {
  const initial = readHrFilters();
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
      const next = readHrFilters();
      replaceAll(next);
      setBranchesState(next.branches);
    });
  }, [replaceAll]);

  const apiParams: HrFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveApiBranch(branches),
  };

  const filterState: HrFilterUrlState = {
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
    setBranches: useCallback((value: string[]) => setBranchesState(value), []),
    apiParams,
    filterState,
  };
}
