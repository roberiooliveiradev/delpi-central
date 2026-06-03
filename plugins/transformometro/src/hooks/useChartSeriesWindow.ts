import { useCallback, useMemo, useState } from "react";

import {
  clampChartOffset,
  getChartSeriesWindow,
  type ChartSeriesWindowState,
} from "../utils/chartSeriesWindow";
import { MAX_PERIOD_BUCKETS } from "../utils/periodBuckets";

export function useChartSeriesWindow<T extends { name?: string; sortKey?: string }>(
  points: T[],
  resetKey: string,
  windowSize: number = MAX_PERIOD_BUCKETS
): ChartSeriesWindowState<T> & {
  goStart: () => void;
  goPrevPage: () => void;
  goNextPage: () => void;
  goEnd: () => void;
  shiftBy: (delta: number) => void;
  setOffset: (value: number) => void;
} {
  const [offset, setOffsetState] = useState(0);
  const [prevResetKey, setPrevResetKey] = useState(resetKey);

  if (resetKey !== prevResetKey) {
    setPrevResetKey(resetKey);
    setOffsetState(0);
  }

  const effectiveOffset = useMemo(
    () => clampChartOffset(offset, points.length, windowSize),
    [offset, points.length, windowSize]
  );

  const maxOffset = Math.max(0, points.length - windowSize);

  const setOffset = useCallback(
    (value: number) => {
      setOffsetState(clampChartOffset(value, points.length, windowSize));
    },
    [points.length, windowSize]
  );

  const windowState = useMemo(
    () => getChartSeriesWindow(points, effectiveOffset, windowSize),
    [points, effectiveOffset, windowSize]
  );

  const goStart = useCallback(() => setOffset(0), [setOffset]);
  const goEnd = useCallback(() => setOffset(maxOffset), [setOffset, maxOffset]);
  const goPrevPage = useCallback(
    () => setOffset(effectiveOffset - windowSize),
    [setOffset, effectiveOffset, windowSize]
  );
  const goNextPage = useCallback(
    () => setOffset(effectiveOffset + windowSize),
    [setOffset, effectiveOffset, windowSize]
  );
  const shiftBy = useCallback(
    (delta: number) => setOffset(effectiveOffset + delta),
    [setOffset, effectiveOffset]
  );

  return {
    ...windowState,
    goStart,
    goPrevPage,
    goNextPage,
    goEnd,
    shiftBy,
    setOffset,
  };
}
