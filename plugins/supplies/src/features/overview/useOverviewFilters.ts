import { useCallback, useEffect, useMemo, useState } from "react";

import { firstDayOfMonthIso, todayIso } from "./overviewContent";
import {
  readOverviewFiltersFromUrl,
  writeOverviewFiltersToUrl,
} from "./overviewFilterUrl";
import { resolvePeriodPreset, type PeriodPresetId } from "./periodPreset";
import {
  formatSuppliesScopeBadge,
  resolveApiBranch,
  resolveEffectiveUnits,
  suppliesUnitOptions,
} from "./suppliesBranchFilters";
import { OVERVIEW_CONTENT } from "./overviewContent";

export type OverviewApiParams = {
  branch?: string;
  from: string;
  to: string;
};

export function useOverviewFilters(allowedUnits: readonly string[]) {
  const fromUrl = useMemo(() => readOverviewFiltersFromUrl(), []);

  const initialPreset: PeriodPresetId =
    fromUrl.period && fromUrl.period !== "custom"
      ? fromUrl.period
      : fromUrl.from || fromUrl.to
        ? "custom"
        : "this_month";

  const initialRange =
    initialPreset !== "custom"
      ? resolvePeriodPreset(initialPreset) ?? {
          from: firstDayOfMonthIso(),
          to: todayIso(),
        }
      : {
          from: fromUrl.from || firstDayOfMonthIso(),
          to: fromUrl.to || todayIso(),
        };

  const [branches, setBranchesState] = useState<string[]>(() => fromUrl.branches ?? []);
  const [from, setFromState] = useState(initialRange.from);
  const [to, setToState] = useState(initialRange.to);
  const [period, setPeriodState] = useState<PeriodPresetId>(initialPreset);

  const setBranches = useCallback(
    (next: string[]) => {
      if (!allowedUnits.length) {
        setBranchesState(next);
        return;
      }
      setBranchesState(next.filter((code) => allowedUnits.includes(code)));
    },
    [allowedUnits],
  );

  const setPeriod = useCallback((next: PeriodPresetId) => {
    setPeriodState(next);
    if (next === "custom") return;
    const range = resolvePeriodPreset(next);
    if (!range) return;
    setFromState(range.from);
    setToState(range.to);
  }, []);

  const setFrom = useCallback((value: string) => {
    setFromState(value);
    setPeriodState("custom");
  }, []);

  const setTo = useCallback((value: string) => {
    setToState(value);
    setPeriodState("custom");
  }, []);

  useEffect(() => {
    writeOverviewFiltersToUrl({ branches, from, to, period });
  }, [branches, from, to, period]);

  useEffect(() => {
    if (!allowedUnits.length) return;
    setBranchesState((prev) => {
      const filtered = prev.filter((code) => allowedUnits.includes(code));
      if (filtered.length === prev.length) return prev;
      return filtered;
    });
  }, [allowedUnits]);

  const unitOptions = useMemo(() => suppliesUnitOptions(allowedUnits), [allowedUnits]);

  const apiParams: OverviewApiParams = useMemo(
    () => ({
      branch: resolveApiBranch(branches, allowedUnits),
      from,
      to,
    }),
    [allowedUnits, branches, from, to],
  );

  const effectiveUnits = useMemo(
    () => resolveEffectiveUnits(branches, allowedUnits),
    [allowedUnits, branches],
  );

  const scopeBadge = useMemo(
    () => formatSuppliesScopeBadge(branches, allowedUnits, OVERVIEW_CONTENT.scopeBadgeAll),
    [allowedUnits, branches],
  );

  return {
    branches,
    from,
    to,
    period,
    setBranches,
    setFrom,
    setTo,
    setPeriod,
    apiParams,
    unitOptions,
    effectiveUnits,
    scopeBadge,
  };
}
