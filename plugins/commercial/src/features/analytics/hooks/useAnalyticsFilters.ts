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
import {
  resolveEffectivePeriodPreset,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "../utils/periodPreset";
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

function sanitizeSellerIds(
  sellerIds: string[],
  access: { allowSellerId: boolean; validSellerIds: readonly string[] },
): string[] {
  if (!access.allowSellerId || sellerIds.length === 0) return [];
  const valid = new Set(access.validSellerIds);
  const seen = new Set<string>();
  const out: string[] = [];
  for (const id of sellerIds) {
    const trimmed = id.trim();
    if (!trimmed || !valid.has(trimmed) || seen.has(trimmed)) continue;
    seen.add(trimmed);
    out.push(trimmed);
  }
  return out;
}

function serializeSellerIdsForApi(sellerIds: string[]): string | undefined {
  if (sellerIds.length === 0) return undefined;
  return sellerIds.join(",");
}

export function useAnalyticsFilters() {
  const initial = readAnalyticsFilters();
  const {
    dateStart,
    dateEnd,
    competence,
    setDateStart: setDateStartLinked,
    setDateEnd: setDateEndLinked,
    setCompetence: setCompetenceLinked,
    replaceAll,
  } = useCompetenceLinkedDates(initial);
  const [branches, setBranchesState] = useState(initial.branches);
  const [customerSegment, setCustomerSegmentState] = useState(initial.customerSegment);
  const [sellerIds, setSellerIdsState] = useState(initial.sellerIds);
  const [storedPeriodPreset, setStoredPeriodPreset] = useState<PeriodPresetId | null>(
    initial.periodPreset,
  );
  const [forceCustomPreset, setForceCustomPreset] = useState(false);

  const clearStoredPreset = useCallback(() => {
    setForceCustomPreset(false);
    setStoredPeriodPreset(null);
  }, []);

  const setDateStart = useCallback(
    (value: string) => {
      clearStoredPreset();
      setDateStartLinked(value);
    },
    [clearStoredPreset, setDateStartLinked],
  );

  const setDateEnd = useCallback(
    (value: string) => {
      clearStoredPreset();
      setDateEndLinked(value);
    },
    [clearStoredPreset, setDateEndLinked],
  );

  const setCompetence = useCallback(
    (value: string) => {
      clearStoredPreset();
      setCompetenceLinked(value);
    },
    [clearStoredPreset, setCompetenceLinked],
  );

  const sellerAccess = usePortfolioSellerAccess();
  const {
    canFilterPortfolios,
    canUseTeamScope,
    filterablePortfolios,
    sellerIdFilter,
    setSellerIdFilter,
  } = usePortfolioScope();

  const effectiveSellerIds = sanitizeSellerIds(sellerIds, sellerAccess);

  useEffect(() => {
    const sanitized = sanitizeSellerIds(sellerIds, sellerAccess);
    if (
      sanitized.length !== sellerIds.length ||
      sanitized.some((id, index) => id !== sellerIds[index])
    ) {
      setSellerIdsState(sanitized);
    }
  }, [sellerAccess, sellerIds]);

  // Sync single selection to portfolio scope; multi/vazio não força Minha Carteira.
  useEffect(() => {
    if (!canFilterPortfolios) return;
    const single = effectiveSellerIds.length === 1 ? effectiveSellerIds[0] : null;
    if (single !== sellerIdFilter) {
      setSellerIdFilter(single);
    }
  }, [canFilterPortfolios, effectiveSellerIds, sellerIdFilter, setSellerIdFilter]);

  const periodPreset: PeriodPresetId = forceCustomPreset
    ? "custom"
    : resolveEffectivePeriodPreset(dateStart, dateEnd, storedPeriodPreset);

  useEffect(() => {
    writeAnalyticsFiltersToUrl({
      dateStart,
      dateEnd,
      competence,
      branches,
      customerSegment,
      sellerIds: effectiveSellerIds,
      periodPreset: forceCustomPreset ? null : storedPeriodPreset,
    });
  }, [
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    effectiveSellerIds,
    storedPeriodPreset,
    forceCustomPreset,
  ]);

  useEffect(() => {
    return subscribeAnalyticsFilterRouteSync(() => {
      const next = readAnalyticsFilters();
      replaceAll(next);
      setBranchesState(next.branches);
      setCustomerSegmentState(next.customerSegment);
      setSellerIdsState(sanitizeSellerIds(next.sellerIds, sellerAccess));
      setStoredPeriodPreset(next.periodPreset);
      setForceCustomPreset(false);
    });
  }, [replaceAll, sellerAccess]);

  const apiParams: AnalyticsFilterParams = {
    start_date: dateStart || undefined,
    end_date: dateEnd || undefined,
    branch: resolveAnalyticsApiBranch(branches),
    customer_segment: customerSegment || undefined,
    seller_id: serializeSellerIdsForApi(effectiveSellerIds),
  };

  const filterState: AnalyticsFilterUrlState = {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    sellerIds: effectiveSellerIds,
    periodPreset: forceCustomPreset ? null : storedPeriodPreset,
  };

  const setPeriodPreset = useCallback(
    (preset: PeriodPresetId) => {
      if (preset === "custom") {
        setForceCustomPreset(true);
        setStoredPeriodPreset(null);
        return;
      }
      const range = resolvePeriodPreset(preset);
      if (!range) return;
      setForceCustomPreset(false);
      setStoredPeriodPreset(preset);
      replaceAll(range);
    },
    [replaceAll],
  );

  return {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    sellerIds: effectiveSellerIds,
    canFilterPortfolios,
    canUseTeamScope,
    filterablePortfolios,
    periodPreset,
    setPeriodPreset,
    setDateStart,
    setDateEnd,
    setCompetence,
    replaceDateFilters: replaceAll,
    setBranches: useCallback((v: string[]) => setBranchesState(v), []),
    setCustomerSegment: useCallback(
      (v: AnalyticsFilterUrlState["customerSegment"]) => setCustomerSegmentState(v),
      [],
    ),
    setSellerIds: useCallback((v: string[]) => setSellerIdsState(v), []),
    apiParams,
    filterState,
  };
}
