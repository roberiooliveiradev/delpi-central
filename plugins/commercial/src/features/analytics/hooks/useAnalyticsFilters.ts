import { useCallback, useEffect, useState } from "react";

import { usePortfolioScope } from "../../../app/PortfolioScopeContext";
import { usePortfolioSellerAccess } from "../../../app/usePortfolioSellerAccess";
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

function sanitizeSellerId(
  sellerId: string | null,
  access: { allowSellerId: boolean; validSellerIds: readonly string[] },
): string | null {
  if (!access.allowSellerId || !sellerId) return null;
  return access.validSellerIds.includes(sellerId) ? sellerId : null;
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
  const [sellerId, setSellerIdState] = useState(initial.sellerId);

  const sellerAccess = usePortfolioSellerAccess();
  const {
    canFilterPortfolios,
    canUseTeamScope,
    filterablePortfolios,
    sellerIdFilter,
    setSellerIdFilter,
  } = usePortfolioScope();

  const effectiveSellerId = sanitizeSellerId(sellerId, sellerAccess);

  useEffect(() => {
    const sanitized = sanitizeSellerId(sellerId, sellerAccess);
    if (sanitized !== sellerId) setSellerIdState(sanitized);
  }, [sellerAccess, sellerId]);

  // Sync analytics seller_id with portfolio scope identity when filtering.
  useEffect(() => {
    if (!canFilterPortfolios) return;
    if (effectiveSellerId !== sellerIdFilter) {
      setSellerIdFilter(effectiveSellerId);
    }
  }, [canFilterPortfolios, effectiveSellerId, sellerIdFilter, setSellerIdFilter]);

  useEffect(() => {
    writeAnalyticsFiltersToUrl({
      dateStart,
      dateEnd,
      competence,
      branches,
      customerSegment,
      sellerId: effectiveSellerId,
    });
  }, [dateStart, dateEnd, competence, branches, customerSegment, effectiveSellerId]);

  useEffect(() => {
    return subscribeAnalyticsFilterRouteSync(() => {
      const next = readAnalyticsFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setCustomerSegmentState(next.customerSegment);
      setSellerIdState(sanitizeSellerId(next.sellerId, sellerAccess));
    });
  }, [replaceAll, sellerAccess]);

  const apiParams: AnalyticsFilterParams = {
    start_date: dateStart || undefined,
    end_date: dateEnd || undefined,
    branch: resolveAnalyticsApiBranch(branches),
    customer_segment: customerSegment || undefined,
    seller_id: effectiveSellerId || undefined,
  };

  const filterState: AnalyticsFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    sellerId: effectiveSellerId,
  };

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    sellerId: effectiveSellerId,
    canFilterPortfolios,
    canUseTeamScope,
    filterablePortfolios,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceDateFilters: replaceAll,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setCustomerSegment: useCallback(
      (v: AnalyticsFilterUrlState["customerSegment"]) => setCustomerSegmentState(v),
      [],
    ),
    setSellerId: useCallback((v: string | null) => setSellerIdState(v), []),
    apiParams,
    filterState,
  };
}
