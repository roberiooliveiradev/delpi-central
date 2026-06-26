import { useCallback, useEffect, useState } from "react";
import {
  getFirstDayOfMonthInputValue,
  getTodayInputValue,
  inputDateToApi,
} from "../utils/dates";
import { resolveApiBranch } from "../utils/branchClientFilters";
import { resolveLinkedDateFilters } from "../utils/competenceFilters";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readQualityFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type QualityFilterUrlState,
} from "../utils/filterUrl";
import type { DateRangeParams } from "../types/ppm";

export function useQualityFilters() {
  const initial = readQualityFilters();
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
      const next = readQualityFilters();
      replaceAll(next);
      setBranchesState(next.branches);
    });
  }, [replaceAll]);

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
    competence,
    branches,
  };

  const resetFilters = useCallback(() => {
    const next = resolveLinkedDateFilters({
      defaultDateStart: getFirstDayOfMonthInputValue(),
      defaultDateEnd: getTodayInputValue(),
    });
    const state: QualityFilterUrlState = {
      ...next,
      branches: [],
    };

    replaceAll(state);
    setBranchesState([]);
    writeFiltersToUrl(state);
  }, [replaceAll]);

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    apiParams,
    filterState,
    resetFilters,
  };
}
