import { useEffect, useMemo, useState } from "react";

import type { ChartGranularity } from "../types/chartGranularity";
import { suggestChartGranularity } from "../utils/suggestChartGranularity";

export type UseChartGranularitySelectionOptions = {
  /** Normaliza a granularidade sugerida (ex.: supplies restringe a month/year). */
  resolveAutoGranularity?: (suggested: ChartGranularity) => ChartGranularity;
};

export function useChartGranularitySelection(
  dateStart?: string,
  dateEnd?: string,
  options?: UseChartGranularitySelectionOptions,
): {
  granularity: ChartGranularity;
  setGranularity: (value: ChartGranularity) => void;
} {
  const resolveAutoGranularity = options?.resolveAutoGranularity;

  const autoGranularity = useMemo(() => {
    const suggested = suggestChartGranularity(dateStart, dateEnd);
    return resolveAutoGranularity ? resolveAutoGranularity(suggested) : suggested;
  }, [dateStart, dateEnd, resolveAutoGranularity]);

  const [granularityOverride, setGranularityOverride] =
    useState<ChartGranularity | null>(null);

  useEffect(() => {
    setGranularityOverride(null);
  }, [dateStart, dateEnd]);

  return {
    granularity: granularityOverride ?? autoGranularity,
    setGranularity: setGranularityOverride,
  };
}
