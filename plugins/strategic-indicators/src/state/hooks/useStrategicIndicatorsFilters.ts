import { useCallback, useEffect, useMemo, useState } from "react";

import {
  buildStrategicIndicatorsMonthRange,
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../../ui/shared/strategicIndicatorsFilters";
import {
  readStrategicIndicatorsFilters,
  writeStrategicIndicatorsFiltersToUrl,
  type StrategicIndicatorsFilterState,
} from "../../ui/shared/strategicIndicatorsFilterUrl";

export function useStrategicIndicatorsFilters() {
  const [referenceMonth, setReferenceMonthState] = useState(
    () => readStrategicIndicatorsFilters().referenceMonth
  );
  const [viewMode, setViewModeState] = useState<StrategicIndicatorsViewMode>(
    () => readStrategicIndicatorsFilters().viewMode
  );
  const [branch, setBranchState] = useState(
    () => readStrategicIndicatorsFilters().branch
  );
  const [monthsToCompare, setMonthsToCompareState] = useState(
    () => readStrategicIndicatorsFilters().monthsToCompare
  );

  const syncToUrl = useCallback((state: StrategicIndicatorsFilterState) => {
    writeStrategicIndicatorsFiltersToUrl(state);
  }, []);

  useEffect(() => {
    syncToUrl({ referenceMonth, viewMode, branch, monthsToCompare });
  }, [referenceMonth, viewMode, branch, monthsToCompare, syncToUrl]);

  useEffect(() => {
    const onPopState = () => {
      const next = readStrategicIndicatorsFilters();
      setReferenceMonthState(next.referenceMonth);
      setViewModeState(next.viewMode);
      setBranchState(next.branch);
      setMonthsToCompareState(next.monthsToCompare);
    };

    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const setReferenceMonth = useCallback((value: string) => {
    setReferenceMonthState(value);
  }, []);

  const setViewMode = useCallback((value: StrategicIndicatorsViewMode) => {
    setViewModeState(value);
  }, []);

  const setBranch = useCallback((value: string) => {
    setBranchState(value);
  }, []);

  const setMonthsToCompare = useCallback((value: number) => {
    setMonthsToCompareState(value);
  }, []);

  const { startDate, endDate } = useMemo(
    () => buildStrategicIndicatorsMonthRange(referenceMonth),
    [referenceMonth]
  );

  const effectiveBranch = useMemo(
    () => resolveStrategicIndicatorsBranch(viewMode, branch),
    [viewMode, branch]
  );

  const filterState: StrategicIndicatorsFilterState = {
    referenceMonth,
    viewMode,
    branch,
    monthsToCompare,
  };

  return {
    referenceMonth,
    viewMode,
    branch,
    monthsToCompare,
    setReferenceMonth,
    setViewMode,
    setBranch,
    setMonthsToCompare,
    startDate,
    endDate,
    effectiveBranch,
    filterState,
  };
}
