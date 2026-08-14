import { useMemo, useState } from "react";
import { NativeCheckboxControl } from "@delpi/plugin-ui/index";

import {
  GroupedColumnSeriesChart,
  type GroupedColumnBarSpec,
} from "./GroupedColumnSeriesChart";
import { CHART_COLORS } from "../constants/chartColors";
import { COMMERCIAL_ROL_SERIES_LABELS } from "../constants/commercialIndicators";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { ROL_CHART_CONTENT } from "../content/rolChartContent";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";
import { formatChartCurrency } from "../utils/format";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 320;

type RolEvolutionChartProps = {
  data: RolSeriesPoint[];
  loading?: boolean;
  onDrillDown: (dateStart: string, dateEnd: string) => void;
};

export function RolEvolutionChart({
  data,
  loading = false,
  onDrillDown,
}: RolEvolutionChartProps) {
  const [showTrend, setShowTrend] = useState(false);

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        periodo: point.periodo,
        rolMatrix: Number(point.rolMatrix) || 0,
        rolBranch: Number(point.rolBranch) || 0,
      })),
    [data],
  );

  const bars = useMemo(
    (): GroupedColumnBarSpec[] => [
      {
        dataKey: "rolMatrix",
        name: COMMERCIAL_ROL_SERIES_LABELS.filial01,
        fill: CHART_COLORS[0],
        trendSource: true,
      },
      {
        dataKey: "rolBranch",
        name: COMMERCIAL_ROL_SERIES_LABELS.filial02,
        fill: CHART_COLORS[1],
        trendSource: true,
      },
    ],
    [],
  );

  if (loading && data.length === 0) {
    return (
      <div className={STATE_BOX_EMPTY} aria-busy="true">
        {ROL_CHART_CONTENT.loading}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={STATE_BOX_EMPTY}>{ROL_CHART_CONTENT.empty}</div>
    );
  }

  return (
    <div className="dc-rol-evolution-chart">
      <div className="dc-field dc-rol-evolution-chart__trend">
        <NativeCheckboxControl
          id="dashboard-rol-trend"
          checked={showTrend}
          onChange={setShowTrend}
          label={ROL_CHART_CONTENT.showTrendLine}
          hint={COMMERCIAL_HELP_TOOLTIPS.charts.rolTrend}
        />
      </div>
      <GroupedColumnSeriesChart
        data={chartData}
        categoryKey="periodo"
        bars={bars}
        height={CHART_HEIGHT}
        showTrend={showTrend}
        formatY={formatChartCurrency}
        formatTooltipValue={formatChartCurrency}
        trendSeriesName={ROL_CHART_CONTENT.trendLineSeriesName}
        onCategoryClick={(category) => {
          const point = data.find((entry) => entry.periodo === category);
          if (point?.dateStart && point?.dateEnd) {
            onDrillDown(point.dateStart, point.dateEnd);
          }
        }}
      />
    </div>
  );
}
