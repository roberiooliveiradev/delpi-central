import type { ReactNode } from "react";

import { ChartGranularityToggle } from "./ChartGranularityToggle";
import type { ChartGranularity } from "../types/chart";

type ChartToolbarProps = {
  granularity: ChartGranularity;
  onGranularityChange: (value: ChartGranularity) => void;
  idPrefix?: string;
  modes?: ChartGranularity[];
  extra?: ReactNode;
};

export function ChartToolbar({
  granularity,
  onGranularityChange,
  idPrefix,
  modes,
  extra,
}: ChartToolbarProps) {
  return (
    <div className="ds-chart-toolbar">
      <ChartGranularityToggle
        idPrefix={idPrefix}
        value={granularity}
        onChange={onGranularityChange}
        modes={modes}
      />
      {extra ? <div className="ds-chart-toolbar__actions">{extra}</div> : null}
    </div>
  );
}
