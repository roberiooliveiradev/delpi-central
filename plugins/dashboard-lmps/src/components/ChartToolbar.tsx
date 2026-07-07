import type { ReactNode } from "react";

import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FieldLabel } from "@delpi/plugin-ui";
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
    <div className="lmps-chart-toolbar">
      <div className="lmps-chart-toolbar__group">
        <FieldLabel
          label="Agrupamento"
          hint={LMPS_HELP_TOOLTIPS.charts.evolutionGranularity} className="lmps-field__label"    />
        <ChartGranularityToggle
          idPrefix={idPrefix}
          value={granularity}
          onChange={onGranularityChange}
          modes={modes}
        />
      </div>
      {extra ? <div className="lmps-chart-toolbar__actions">{extra}</div> : null}
    </div>
  );
}
