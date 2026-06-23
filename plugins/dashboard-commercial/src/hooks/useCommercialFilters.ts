import { useCallback, useEffect, useState } from "react";
import { inputDateToApi } from "../utils/dates";
import { resolveCommercialApiBranch } from "../utils/commercialClientFilters";
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
  const [branches, setBranchesState] = useState(
    () => readCommercialFilters().branches
  );
  const [customerSegment, setCustomerSegmentState] = useState(
    () => readCommercialFilters().customerSegment
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branches, customerSegment });
  }, [dateStart, dateEnd, branches, customerSegment]);

  useEffect(() => {
    const onPopState = () => {
      const next = readCommercialFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchesState(next.branches);
      setCustomerSegmentState(next.customerSegment);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: CommercialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: resolveCommercialApiBranch(branches),
    customer_segment: customerSegment || undefined,
  };

  const filterState: CommercialFilterUrlState = {
    dateStart,
    dateEnd,
    branches,
    customerSegment,
  };

  return {
    dateStart,
    dateEnd,
    branches,
    customerSegment,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
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
