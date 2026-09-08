import { useEffect, useMemo, useState } from "react";
import { ChartViewShell, MultiTypeSeriesChart } from "@delpi/plugin-ui/index";

import { getOtdSeries } from "../../api/otdSeries";
import {
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { mapOverviewFetchError, OVERVIEW_CONTENT } from "./overviewContent";
import type { OverviewApiParams } from "./useOverviewFilters";

type OverviewOtdSeriesChartProps = {
  filters: OverviewApiParams;
};

const CHART_HEIGHT = 280;

export function OverviewOtdSeriesChart({ filters }: OverviewOtdSeriesChartProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [partialNote, setPartialNote] = useState<string | null>(null);
  const [points, setPoints] = useState<Array<{ period: string; otdPct: number }>>([]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setPartialNote(null);
    getOtdSeries(
      {
        branch: filters.branch,
        from: filters.from,
        to: filters.to,
        granularity: "month",
      },
      controller.signal,
    )
      .then((payload) => {
        const next = (payload.points ?? [])
          .filter((point) => point.otdPct != null && Number.isFinite(point.otdPct))
          .map((point) => ({
            period: point.period,
            otdPct: Number(point.otdPct),
          }));
        setPoints(next);
        if ((payload.partialFailures?.length ?? 0) > 0) {
          setPartialNote(OVERVIEW_CONTENT.partialNote);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setPoints([]);
        const message = err instanceof Error ? err.message : OVERVIEW_CONTENT.otdChartError;
        setError(mapOverviewFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters.branch, filters.from, filters.to]);

  const series = useMemo(
    () => [
      {
        dataKey: "otdPct",
        name: OVERVIEW_CONTENT.otdSeriesLabel,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
    ],
    [],
  );

  const formatPct = (value: number) =>
    `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

  return (
    <div className="sp-overview__chart">
      <p className="sp-overview__chart-hint">{SP_HELP.overviewOtdChart}</p>
      {loading ? (
        <SuppliesLoadingCard title={OVERVIEW_CONTENT.otdChartLoading} variant="panel" />
      ) : null}
      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && partialNote ? (
        <SuppliesStateBanner>{partialNote}</SuppliesStateBanner>
      ) : null}
      {!loading && !error && points.length === 0 ? (
        <SuppliesEmptyState
          title={OVERVIEW_CONTENT.otdChartEmptyTitle}
          message={OVERVIEW_CONTENT.otdChartEmptyMessage}
        />
      ) : null}
      {!loading && !error && points.length > 0 ? (
        <ChartViewShell prefix="sp">
          <MultiTypeSeriesChart
            data={points}
            categoryKey="period"
            series={series}
            chartType="line"
            height={CHART_HEIGHT}
            formatY={formatPct}
            formatTooltipValue={formatPct}
            showLegend
          />
        </ChartViewShell>
      ) : null}
    </div>
  );
}
