import { useEffect, useMemo, useRef, useState } from "react";
import {
  EmptyState,
  NativeCheckboxControl,
  runTabularExport,
  type ChartGranularity,
} from "@delpi/plugin-ui/index";

import { getCommercialRolSeries } from "../../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  CommercialChartToolbar,
  CommercialLoadingCard,
  CommercialTabularExportButtons,
  useChartGranularitySelection,
} from "../../../app/commercialUi";
import {
  GroupedColumnSeriesChart,
  type GroupedColumnBarSpec,
} from "../../../components/GroupedColumnSeriesChart";
import { buildOverviewRolSeriesPayload } from "../../overview/overviewExportBuilders";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import type {
  AnalyticsFilterParams,
  CommercialRolSeriesPoint,
} from "../../../types/analytics";
import { formatCurrency } from "../../../utils/format";
import { ANALYTICS_ROL_SERIES_LABELS } from "../utils/analyticsBranchFilters";
import {
  mergeSeriesWithPriorYear,
  shiftPeriodRangeByYears,
} from "../utils/periodShift";

const CHART_HEIGHT = 320;

const ROL_GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];

type RolChartPoint = CommercialRolSeriesPoint & {
  rol_matrix_prior?: number | null;
  rol_branch_prior?: number | null;
};

type RolSeriesChartProps = {
  filters: Pick<
    AnalyticsFilterParams,
    "start_date" | "end_date" | "customer_segment" | "seller_id"
  >;
  /** Clique no ponto → filtra o período analytics ao intervalo do bucket. */
  onDrillDown?: (dateStart: string, dateEnd: string) => void;
  /** Expõe pontos carregados (export / testes). */
  onPointsChange?: (points: CommercialRolSeriesPoint[]) => void;
};

function formatChartCurrency(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return formatCurrency(value);
}

/**
 * Evolução de ROL — séries Santa Catarina / Espírito Santo, toolbar Dia–Ano,
 * YoY em colunas e tendência linear opcional por filial atual.
 */
export function AnalyticsRolSeriesChart({
  filters,
  onDrillDown,
  onPointsChange,
}: RolSeriesChartProps) {
  const { granularity, setGranularity } = useChartGranularitySelection(
    filters.start_date,
    filters.end_date,
  );
  const [comparePriorYear, setComparePriorYear] = useState(false);
  const [showTrend, setShowTrend] = useState(false);
  const [points, setPoints] = useState<RolChartPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;
  const onPointsChangeRef = useRef(onPointsChange);
  onPointsChangeRef.current = onPointsChange;

  const yoyActive = comparePriorYear;

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const currentPromise = getCommercialRolSeries(
      { ...filters, granularity },
      controller.signal,
    );

    const priorRange =
      yoyActive && filters.start_date && filters.end_date
        ? shiftPeriodRangeByYears(
            { start_date: filters.start_date, end_date: filters.end_date },
            -1,
          )
        : null;

    const priorPromise = priorRange
      ? getCommercialRolSeries(
          {
            ...filters,
            start_date: priorRange.start_date,
            end_date: priorRange.end_date,
            granularity,
          },
          controller.signal,
        )
      : Promise.resolve(null);

    void Promise.all([currentPromise, priorPromise])
      .then(([currentData, priorData]) => {
        if (controller.signal.aborted) return;
        const current = currentData.points ?? [];
        const prior = priorData?.points ?? [];
        const next: RolChartPoint[] = yoyActive
          ? mergeSeriesWithPriorYear(current, prior, (p) => ({
              rol_matrix_prior: p?.rol_matrix ?? null,
              rol_branch_prior: p?.rol_branch ?? null,
            }))
          : current;
        setPoints(next);
        onPointsChangeRef.current?.(current);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : emptyCopy.rolError);
        setPoints([]);
        onPointsChangeRef.current?.([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    emptyCopy.rolError,
    filters.start_date,
    filters.end_date,
    filters.customer_segment,
    filters.seller_id,
    granularity,
    yoyActive,
  ]);

  const exportIncludePrior = yoyActive;

  const priorLabels = useMemo(
    () => ({
      unit01: `${ANALYTICS_ROL_SERIES_LABELS.unit01} (ano ant.)`,
      unit02: `${ANALYTICS_ROL_SERIES_LABELS.unit02} (ano ant.)`,
    }),
    [],
  );

  const bars = useMemo((): GroupedColumnBarSpec[] => {
    const list: GroupedColumnBarSpec[] = [
      {
        dataKey: "rol_matrix",
        name: ANALYTICS_ROL_SERIES_LABELS.unit01,
        fill: "var(--chart-1, #089bdb)",
        trendSource: true,
      },
      {
        dataKey: "rol_branch",
        name: ANALYTICS_ROL_SERIES_LABELS.unit02,
        fill: "var(--chart-2, #10b981)",
        trendSource: true,
      },
    ];
    if (yoyActive) {
      list.push(
        {
          dataKey: "rol_matrix_prior",
          name: priorLabels.unit01,
          fill: "var(--chart-3, #94a3b8)",
        },
        {
          dataKey: "rol_branch_prior",
          name: priorLabels.unit02,
          fill: "var(--chart-4, #64748b)",
        },
      );
    }
    return list;
  }, [priorLabels.unit01, priorLabels.unit02, yoyActive]);

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.periodo,
        rol_matrix: Number(point.rol_matrix) || 0,
        rol_branch: Number(point.rol_branch) || 0,
        rol_matrix_prior:
          point.rol_matrix_prior == null ? null : Number(point.rol_matrix_prior) || 0,
        rol_branch_prior:
          point.rol_branch_prior == null ? null : Number(point.rol_branch_prior) || 0,
      })),
    [points],
  );

  return (
    <div className="cm-rol-series">
      <div className="cm-rol-series__toolbar">
        <p className="cm-rol-series__hint">{CM_HELP.overview.rolSeries}</p>
        <CommercialTabularExportButtons
          compact
          disabled={points.length === 0 || loading}
          onExport={(format) => {
            runTabularExport({
              kind: "table",
              format,
              payload: buildOverviewRolSeriesPayload(points, {
                includePriorYear: exportIncludePrior,
              }),
            });
          }}
        />
      </div>
      <div className="cm-rol-series__toolbar">
        <CommercialChartToolbar
          granularity={granularity}
          onGranularityChange={setGranularity}
          options={ROL_GRANULARITY_OPTIONS}
          modes={["day", "week", "month", "year"]}
        />
        <NativeCheckboxControl
          id="overview-rol-yoy"
          checked={yoyActive}
          onChange={setComparePriorYear}
          label={ANALYTICS_CONTENT.overview.comparePriorYear}
          hint={CM_HELP.overview.rolSeriesYoy}
        />
        <NativeCheckboxControl
          id="overview-rol-trend"
          checked={showTrend}
          onChange={setShowTrend}
          label={CUSTOMER_BILLING_CONTENT.showTrendLine}
          hint={CM_HELP.customerDetail.billingSeriesTrend}
        />
      </div>
      {loading ? (
        <CommercialLoadingCard title={emptyCopy.rolLoading} variant="panel" />
      ) : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}
      {!loading && !error && points.length === 0 ? (
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={emptyCopy.rolTitle}
          defaultMessage={emptyCopy.rolMessage}
        />
      ) : null}
      {!loading && !error && points.length > 0 ? (
        <div className="cm-chart-wrap" style={{ width: "100%", height: CHART_HEIGHT }}>
          <GroupedColumnSeriesChart
            data={chartData}
            categoryKey="periodo"
            bars={bars}
            height={CHART_HEIGHT}
            showTrend={showTrend}
            formatY={formatChartCurrency}
            formatTooltipValue={formatChartCurrency}
            onCategoryClick={
              onDrillDown
                ? (category) => {
                    const point = points.find((entry) => entry.periodo === category);
                    if (point?.start_date && point?.end_date) {
                      onDrillDown(point.start_date, point.end_date);
                    }
                  }
                : undefined
            }
          />
        </div>
      ) : null}
    </div>
  );
}
