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
import type { PpmProductScope } from "../utils/ppmProductScope";
import { resolvePpmProductPrefix } from "../utils/ppmProductScope";

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
  const [ppmProductScope, setPpmProductScopeState] = useState<PpmProductScope>(
    initial.ppmProductScope
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches, ppmProductScope });
  }, [dateStart, dateEnd, competence, branches, ppmProductScope]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readQualityFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setPpmProductScopeState(next.ppmProductScope);
    });
  }, [replaceAll]);

  const setBranches = useCallback((value: string[]) => {
    setBranchesState(value);
  }, []);

  const setPpmProductScope = useCallback((value: PpmProductScope) => {
    setPpmProductScopeState(value);
  }, []);

  const apiParams: DateRangeParams = {
    branch: resolveApiBranch(branches),
    date_start: inputDateToApi(dateStart),
    date_end: inputDateToApi(dateEnd),
  };

  const ppmApiParams: DateRangeParams = {
    ...apiParams,
    product_prefix: resolvePpmProductPrefix(ppmProductScope),
  };

  const filterState: QualityFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    ppmProductScope,
  };

  const resetFilters = useCallback(() => {
    const next = resolveLinkedDateFilters({
      defaultDateStart: getFirstDayOfMonthInputValue(),
      defaultDateEnd: getTodayInputValue(),
    });
    const state: QualityFilterUrlState = {
      ...next,
      branches: [],
      ppmProductScope: "all",
    };

    replaceAll(state);
    setBranchesState([]);
    setPpmProductScopeState("all");
    writeFiltersToUrl(state);
  }, [replaceAll]);

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    ppmProductScope,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setPpmProductScope,
    apiParams,
    ppmApiParams,
    filterState,
    resetFilters,
  };
}
