import { useCallback, useEffect, useState } from "react";
import { inputDateToApi } from "../utils/dates";
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
  const [branch, setBranchState] = useState(() => readCommercialFilters().branch);
  const [customerSegment, setCustomerSegmentState] = useState(
    () => readCommercialFilters().customerSegment
  );

  useEffect(() => {
    writeFiltersToUrl({ dateStart, dateEnd, branch, customerSegment });
  }, [dateStart, dateEnd, branch, customerSegment]);

  useEffect(() => {
    const onPopState = () => {
      const next = readCommercialFilters();
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setBranchState(next.branch);
      setCustomerSegmentState(next.customerSegment);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const apiParams: CommercialFilterParams = {
    start_date: inputDateToApi(dateStart),
    end_date: inputDateToApi(dateEnd),
    branch: branch || undefined,
    customer_segment: customerSegment || undefined,
  };

  const filterState: CommercialFilterUrlState = {
    dateStart,
    dateEnd,
    branch,
    customerSegment,
  };

  return {
    dateStart,
    dateEnd,
    branch,
    customerSegment,
    setDateStart: useCallback((v: string) => setDateStartState(v), []),
    setDateEnd: useCallback((v: string) => setDateEndState(v), []),
    setBranch: useCallback((v: string) => setBranchState(v), []),
    setCustomerSegment: useCallback(
      (v: CommercialFilterUrlState["customerSegment"]) =>
        setCustomerSegmentState(v),
      []
    ),
    apiParams,
    filterState,
  };
}
