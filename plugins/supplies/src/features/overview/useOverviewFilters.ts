import { useCallback, useEffect, useMemo, useState } from "react";

import { firstDayOfMonthIso, todayIso } from "./overviewContent";
import {
  readOverviewFiltersFromUrl,
  writeOverviewFiltersToUrl,
} from "./overviewFilterUrl";
import {
  resolvePeriodPreset,
  type PeriodPresetId,
} from "./periodPreset";

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

  const [branch, setBranchState] = useState(() => {
    if (fromUrl.branch && allowedUnits.includes(fromUrl.branch)) {
      return fromUrl.branch;
    }
    return fromUrl.branch || "";
  });
  const [from, setFromState] = useState(initialRange.from);
  const [to, setToState] = useState(initialRange.to);
  const [period, setPeriodState] = useState<PeriodPresetId>(initialPreset);

  const setBranch = useCallback(
    (value: string) => {
      if (value && allowedUnits.length > 0 && !allowedUnits.includes(value)) {
        setBranchState("");
        return;
      }
      setBranchState(value);
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
    writeOverviewFiltersToUrl({ branch, from, to, period });
  }, [branch, from, to, period]);

  useEffect(() => {
    if (!allowedUnits.length) return;
    if (branch && !allowedUnits.includes(branch)) {
      setBranchState("");
      return;
    }
    if (!branch && fromUrl.branch && allowedUnits.includes(fromUrl.branch)) {
      setBranchState(fromUrl.branch);
    }
  }, [allowedUnits, branch, fromUrl.branch]);

  const apiParams: OverviewApiParams = useMemo(
    () => ({
      branch: branch || undefined,
      from,
      to,
    }),
    [branch, from, to],
  );

  return {
    branch,
    from,
    to,
    period,
    setBranch,
    setFrom,
    setTo,
    setPeriod,
    apiParams,
  };
}
