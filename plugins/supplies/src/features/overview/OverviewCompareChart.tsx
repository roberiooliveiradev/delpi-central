import { useMemo } from "react";
import { ChartViewShell, MultiTypeSeriesChart } from "@delpi/plugin-ui/index";

import type { OverviewKpiCard } from "../../api/overview";
import { SuppliesEmptyState } from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { OVERVIEW_CONTENT } from "./overviewContent";

type OverviewCompareChartProps = {
  kpis: OverviewKpiCard[];
};

const CHART_HEIGHT = 260;

export function OverviewCompareChart({ kpis }: OverviewCompareChartProps) {
  const rows = useMemo(
    () =>
      kpis
        .filter(
          (kpi) =>
            kpi.temporalNature === "interval" &&
            kpi.status === "available" &&
            kpi.value != null &&
            Number.isFinite(kpi.value) &&
            kpi.meta != null &&
            Number.isFinite(kpi.meta),
        )
        .map((kpi) => ({
          label: kpi.title,
          value: Number(kpi.value),
          meta: Number(kpi.meta),
        })),
    [kpis],
  );

  const series = useMemo(
    () => [
      {
        dataKey: "value",
        name: OVERVIEW_CONTENT.compareValueLabel,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
      {
        dataKey: "meta",
        name: OVERVIEW_CONTENT.compareMetaLabel,
        fill: "var(--delpi-chart-series-2, #94a3b8)",
      },
    ],
    [],
  );

  return (
    <div className="sp-overview__chart">
      <p className="sp-overview__chart-hint">{SP_HELP.overviewCompareChart}</p>
      {rows.length === 0 ? (
        <SuppliesEmptyState
          title={OVERVIEW_CONTENT.compareEmptyTitle}
          message={OVERVIEW_CONTENT.compareEmptyMessage}
        />
      ) : (
        <ChartViewShell prefix="sp">
          <MultiTypeSeriesChart
            data={rows}
            categoryKey="label"
            series={series}
            chartType="column"
            height={CHART_HEIGHT}
            showLegend
          />
        </ChartViewShell>
      )}
    </div>
  );
}
