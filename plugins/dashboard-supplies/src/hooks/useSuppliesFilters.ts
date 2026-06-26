import { useCallback, useEffect, useState } from "react";
import type { SuppliesFilterParams } from "../types/supplies";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { inputDateToApi } from "../utils/dates";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readSuppliesFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type SuppliesFilterUrlState,
} from "../utils/filterUrl";

export function useSuppliesFilters() {
  const initial = readSuppliesFilters();
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
  const [location, setLocationState] = useState(initial.location);

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches, location });
  }, [dateStart, dateEnd, competence, branches, location]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readSuppliesFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setLocationState(next.location);
    });
  }, [replaceAll]);

  const resolvedBranch = resolveApiBranch(branches);

  const periodParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const stockParams: SuppliesFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolvedBranch,
    location: location || undefined,
  };

  const filterState: SuppliesFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    location,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setLocation: useCallback((v: string) => setLocationState(v), []),
    periodParams,
    stockParams,
    filterState,
  };
}
