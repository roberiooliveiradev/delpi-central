import { useMemo } from "react";
import {
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  PERIOD_COMPARE_TYPES,
  applySeriesFillPreferences,
  runTabularExport,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import type { OverviewKpiCard } from "../../api/overview";
import {
  SuppliesEmptyState,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { OVERVIEW_CONTENT } from "./overviewContent";

type OverviewCompareChartProps = {
  kpis: OverviewKpiCard[];
  storageKey?: string;
};

const CHART_HEIGHT = 320;

export function OverviewCompareChart({
  kpis,
  storageKey = "supplies:overview:compare",
}: OverviewCompareChartProps) {
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey,
    defaults: { chartType: "column" },
    allowedChartTypes: PERIOD_COMPARE_TYPES,
  });
  const chartType = preferences.chartType ?? "column";

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

  const baseSeries = useMemo(
    (): MultiTypeSeriesSpec[] => [
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

  const series = useMemo(
    () => applySeriesFillPreferences(baseSeries, preferences.seriesFills),
    [baseSeries, preferences.seriesFills],
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
        <ChartViewShell
          prefix="sp"
          typeToggleLabel={OVERVIEW_CONTENT.chartTypeLabel}
          seriesColorsLabel={OVERVIEW_CONTENT.chartSeriesColorsLabel}
          typeToggle={
            <ChartTypeSegmentToggle
              family="period_compare"
              value={chartType}
              onChange={setChartType}
              idPrefix="supplies-compare-type"
              prefix="sp"
              portalScopeClassName={SP_PORTAL_SCOPE}
            />
          }
          seriesColors={
            <ChartSeriesColorsPopover
              idPrefix="supplies-compare-colors"
              portalScopeClassName={SP_PORTAL_SCOPE}
              series={series}
              values={preferences.seriesFills}
              summaryLabel={OVERVIEW_CONTENT.chartSeriesColorsEmpty}
              panelTitle={OVERVIEW_CONTENT.chartSeriesColorsPanelTitle}
              triggerAriaLabel={OVERVIEW_CONTENT.chartSeriesColorsTriggerAria}
              resetLabel={OVERVIEW_CONTENT.chartSeriesColorsReset}
              onChange={(dataKey, color) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesFills: { ...(prev.seriesFills ?? {}), [dataKey]: color },
                }))
              }
              onReset={() => setPreferences((prev) => ({ ...prev, seriesFills: undefined }))}
            />
          }
          exportActions={
            <SuppliesTabularExportButtons
              compact
              disabled={rows.length === 0}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title: OVERVIEW_CONTENT.compareTitle,
                    columns: [
                      { key: "label", label: "Indicador" },
                      { key: "value", label: OVERVIEW_CONTENT.compareValueLabel },
                      { key: "meta", label: OVERVIEW_CONTENT.compareMetaLabel },
                    ],
                    rows,
                  },
                });
              }}
            />
          }
        >
          <MultiTypeSeriesChart
            data={rows}
            categoryKey="label"
            series={series}
            chartType={chartType}
            height={CHART_HEIGHT}
            showLegend
          />
        </ChartViewShell>
      )}
    </div>
  );
}
