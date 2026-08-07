import { useCallback, useEffect, useState } from "react";

import type { AnalyticsFilterParams } from "../../../types/analytics";
import {
  applyCompetenceChange,
  applyDateEndChange,
  applyDateStartChange,
  type LinkedDateFilters,
} from "../utils/competenceFilters";
import { resolveAnalyticsApiBranch } from "../utils/analyticsBranchFilters";
import {
  readAnalyticsFilters,
  subscribeAnalyticsFilterRouteSync,
  writeAnalyticsFiltersToUrl,
  type AnalyticsFilterUrlState,
} from "../utils/analyticsFilterUrl";

function useCompetenceLinkedDates(initial: LinkedDateFilters) {
  const [dateStart, setDateStartState] = useState(initial.dateStart);
  const [dateEnd, setDateEndState] = useState(initial.dateEnd);
  const [competence, setCompetenceState] = useState(initial.competence);

  const replaceAll = useCallback((next: LinkedDateFilters) => {
    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
    setCompetenceState(next.competence);
  }, []);

  const setCompetence = useCallback((value: string) => {
    if (!value) {
      setCompetenceState("");
      return;
    }
    const next = applyCompetenceChange(value);
    setCompetenceState(next.competence);
    setDateStartState(next.dateStart);
    setDateEndState(next.dateEnd);
  }, []);

  const setDateStart = useCallback(
    (value: string) => {
      const next = applyDateStartChange(value, dateEnd);
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setCompetenceState(next.competence);
    },
    [dateEnd],
  );

  const setDateEnd = useCallback(
    (value: string) => {
      const next = applyDateEndChange(dateStart, value);
      setDateStartState(next.dateStart);
      setDateEndState(next.dateEnd);
      setCompetenceState(next.competence);
    },
    [dateStart],
  );

  return {
    dateStart,
    dateEnd,
    competence,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceAll,
  };
}

export function useAnalyticsFilters() {
  const initial = readAnalyticsFilters();
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
  const [customerSegment, setCustomerSegmentState] = useState(initial.customerSegment);

  useEffect(() => {
    writeAnalyticsFiltersToUrl({
      dateStart,
      dateEnd,
      competence,
      branches,
      customerSegment,
    });
  }, [dateStart, dateEnd, competence, branches, customerSegment]);

  useEffect(() => {
    return subscribeAnalyticsFilterRouteSync(() => {
      const next = readAnalyticsFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setCustomerSegmentState(next.customerSegment);
    });
  }, [replaceAll]);

  const apiParams: AnalyticsFilterParams = {
    start_date: dateStart || undefined,
    end_date: dateEnd || undefined,
    branch: resolveAnalyticsApiBranch(branches),
    customer_segment: customerSegment || undefined,
  };

  const filterState: AnalyticsFilterUrlState = {
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
      (v: AnalyticsFilterUrlState["customerSegment"]) => setCustomerSegmentState(v),
      [],
    ),
    apiParams,
    filterState,
  };
}
