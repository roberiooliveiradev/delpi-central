/**
 * U15R R1 — «Evolução por dia» no padrão do Comercial:
 * ChartViewShell + ChartTypeSegmentToggle (period_compare) + MultiTypeSeriesChart.
 */
import { useMemo } from "react";
import {
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  PERIOD_COMPARE_TYPES,
  applySeriesViewPreferences,
  buildChartSeriesConfigItems,
  omitRecordKey,
  patchSeriesTrendStyle,
  resetSeriesViewPreferences,
  runTabularExport,
  seriesViewHasOverrides,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
  type TableExportPayload,
} from "@delpi/plugin-ui/index";

import {
  CF_PORTAL_SCOPE,
  CfEmptyState,
  CfTabularExportButtons,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import type { EntryAuditDailyChartPoint } from "./entryAuditPresentation";

const CHART_HEIGHT = 280;
const STORAGE_KEY = "controllership-finance:entry-audit:daily";
const COLOR_CURRENT = "var(--delpi-ui-accent, #2563eb)";
const COLOR_PRIOR =
  "color-mix(in srgb, var(--delpi-ui-accent, #2563eb) 56%, var(--delpi-ui-muted, #94a3b8))";
const COLOR_SELECTED = "var(--delpi-ui-accent, #2563eb)";
const COLOR_DIM =
  "color-mix(in srgb, var(--delpi-ui-muted, #94a3b8) 72%, transparent)";

const CHART_COPY = {
  typeLabel: "Tipo",
  seriesColorsLabel: "Séries",
  seriesColorsEmpty: "Séries",
  seriesColorsPanelTitle: "Configurar séries",
  seriesColorsReset: "Restaurar todas",
  seriesColorsResetSeries: "Restaurar padrão",
  seriesColorsTriggerAria: "Configurar séries do gráfico",
} as const;

type Props = {
  points: EntryAuditDailyChartPoint[];
  includePrevious: boolean;
  previousPeriodLegend: string | null;
  selectedDay: string;
  onSelectDay: (dayIso: string) => void;
};

function formatCount(value: number): string {
  return value.toLocaleString("pt-BR");
}

function buildExportPayload(
  rows: Array<{
    periodo: string;
    day: string;
    atual: number;
    anterior?: number;
  }>,
  includePrevious: boolean,
): TableExportPayload {
  const columns = [
    { key: "dia", label: "Dia" },
    { key: "data", label: "Data" },
    { key: "atual", label: "Este período" },
    ...(includePrevious
      ? [{ key: "anterior", label: "Período anterior" }]
      : []),
  ];
  return {
    title: "Evolução por dia",
    columns,
    rows: rows.map((row) => ({
      dia: row.periodo,
      data: row.day,
      atual: formatCount(row.atual),
      ...(includePrevious
        ? { anterior: formatCount(Number(row.anterior) || 0) }
        : {}),
    })),
  };
}

export function EntryAuditDailyEvolutionChart({
  points,
  includePrevious,
  previousPeriodLegend,
  selectedDay,
  onSelectDay,
}: Props) {
  const { preferences, setPreferences, setChartType } =
    usePersistedChartPreferences({
      storageKey: STORAGE_KEY,
      defaults: { chartType: "column" },
      allowedChartTypes: PERIOD_COMPARE_TYPES,
    });
  const chartType = preferences.chartType ?? "column";

  const chartData = useMemo(
    () =>
      points.map((point) => {
        const selected = Boolean(selectedDay) && point.day === selectedDay;
        return {
          periodo: point.name,
          day: point.day,
          atual: point.current,
          ...(includePrevious ? { anterior: point.previous ?? 0 } : {}),
          ...(selectedDay
            ? { fill: selected ? COLOR_SELECTED : COLOR_DIM }
            : {}),
        };
      }),
    [points, includePrevious, selectedDay],
  );

  const periodByLabel = useMemo(() => {
    const map = new Map<string, string>();
    for (const point of points) map.set(point.name, point.day);
    return map;
  }, [points]);

  const baseSeries = useMemo((): MultiTypeSeriesSpec[] => {
    const series: MultiTypeSeriesSpec[] = [
      {
        dataKey: "atual",
        name: "Este período",
        fill: COLOR_CURRENT,
      },
    ];
    if (includePrevious) {
      series.push({
        dataKey: "anterior",
        name: previousPeriodLegend
          ? `Período anterior (${previousPeriodLegend})`
          : "Período anterior",
        fill: COLOR_PRIOR,
      });
    }
    return series;
  }, [includePrevious, previousPeriodLegend]);

  const series = useMemo(
    () => applySeriesViewPreferences(baseSeries, preferences),
    [baseSeries, preferences],
  );
  const seriesConfigItems = useMemo(
    () => buildChartSeriesConfigItems(baseSeries, preferences),
    [baseSeries, preferences],
  );

  const hasValues = points.some(
    (point) =>
      point.current > 0 ||
      (includePrevious && (point.previous ?? 0) > 0),
  );

  return (
    <div
      className="cf-analysis-daily-chart"
      role="group"
      aria-label="Evolução diária de ocorrências"
      data-testid="entry-audit-daily-evolution"
    >
      {!hasValues ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Sem evolução diária para exibir."
        />
      ) : (
        <ChartViewShell
          prefix="cf"
          seriesColorsLabel={CHART_COPY.seriesColorsLabel}
          typeToggleLabel={CHART_COPY.typeLabel}
          typeToggle={
            <ChartTypeSegmentToggle
              family="period_compare"
              value={chartType}
              onChange={setChartType}
              idPrefix="entry-audit-daily-type"
              prefix="cf"
              portalScopeClassName={CF_PORTAL_SCOPE}
            />
          }
          exportActions={
            <CfTabularExportButtons
              compact
              disabled={!hasValues}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: buildExportPayload(chartData, includePrevious),
                });
              }}
            />
          }
          seriesColors={
            <ChartSeriesColorsPopover
              idPrefix="entry-audit-daily-colors"
              portalScopeClassName={CF_PORTAL_SCOPE}
              series={seriesConfigItems}
              values={preferences.seriesFills}
              hasOverrides={seriesViewHasOverrides(preferences)}
              summaryLabel={CHART_COPY.seriesColorsEmpty}
              panelTitle={CHART_COPY.seriesColorsPanelTitle}
              triggerAriaLabel={CHART_COPY.seriesColorsTriggerAria}
              resetLabel={CHART_COPY.seriesColorsReset}
              resetSeriesLabel={CHART_COPY.seriesColorsResetSeries}
              onChange={(dataKey, color) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesFills: { ...(prev.seriesFills ?? {}), [dataKey]: color },
                }))
              }
              onVisibleChange={(dataKey, visible) =>
                setPreferences((prev) => ({
                  ...prev,
                  hiddenSeries: visible
                    ? omitRecordKey(prev.hiddenSeries, dataKey)
                    : { ...(prev.hiddenSeries ?? {}), [dataKey]: true },
                }))
              }
              onTrendChange={(dataKey, enabled) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesTrend: { ...(prev.seriesTrend ?? {}), [dataKey]: enabled },
                }))
              }
              onTrendStyleChange={(dataKey, style) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesTrendStyles: patchSeriesTrendStyle(
                    prev.seriesTrendStyles,
                    dataKey,
                    style,
                  ),
                }))
              }
              onResetSeries={(dataKey) =>
                setPreferences((prev) => resetSeriesViewPreferences(prev, dataKey))
              }
              onReset={() =>
                setPreferences((prev) => resetSeriesViewPreferences(prev))
              }
            />
          }
        >
          <MultiTypeSeriesChart
            data={chartData}
            categoryKey="periodo"
            categoryFillKey={selectedDay ? "fill" : undefined}
            series={series}
            chartType={chartType}
            height={CHART_HEIGHT}
            showLegend={includePrevious}
            formatY={formatCount}
            formatTooltipValue={formatCount}
            onCategoryClick={(category) => {
              const day = periodByLabel.get(category) ?? "";
              if (!day) return;
              onSelectDay(day === selectedDay ? "" : day);
            }}
          />
        </ChartViewShell>
      )}
    </div>
  );
}
