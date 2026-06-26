import { useCallback, useEffect, useState } from "react";
import { inputDateToApi } from "../utils/dates";
import { resolveCommercialApiBranch } from "../utils/commercialClientFilters";
import { useCompetenceLinkedDates } from "./useCompetenceLinkedDates";
import {
  readCommercialFilters,
  subscribeFilterRouteSync,
  writeFiltersToUrl,
  type CommercialFilterUrlState,
} from "../utils/filterUrl";
import type { CommercialFilterParams } from "../types/commercial";

export function useCommercialFilters() {
  const initial = readCommercialFilters();
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
  const [customerSegment, setCustomerSegmentState] = useState(
    initial.customerSegment
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, competence, branches, customerSegment });
  }, [dateStart, dateEnd, competence, branches, customerSegment]);

  useEffect(() => {
    return subscribeFilterRouteSync(() => {
      const next = readCommercialFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setCustomerSegmentState(next.customerSegment);
    });
  }, [replaceAll]);

  const apiParams: CommercialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveCommercialApiBranch(branches),
    customer_segment: customerSegment || undefined,
  };

  const filterState: CommercialFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setCustomerSegment: useCallback(
      (v: CommercialFilterUrlState["customerSegment"]) =>
        setCustomerSegmentState(v),
      []
    ),
    apiParams,
    filterState,
  };
}
