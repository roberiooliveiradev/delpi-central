/** Composição gráfica corporativa da Engenharia — mesmo padrão do Portal
 * Comercial: `ChartViewShell` (toolbar) + `ChartTypeSegmentToggle` +
 * `ChartOverlayOptionsPopover` + `ChartSeriesColorsPopover` +
 * `TabularExportButtons` + `MultiTypeSeriesChart`, com preferências
 * persistidas via `usePersistedChartPreferences` em namespace próprio
 * (`engineering:routing:*`) — separado do rascunho técnico do estudo.
 *
 * Valores chegam em MINUTOS (fonte oficial intacta); a conversão
 * s/min acontece só aqui, na camada de apresentação. */

import { useMemo } from "react";
import {
  CATEGORICAL_TYPES,
  ChartOverlayOptionsPopover,
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  TabularExportButtons,
  applySeriesViewPreferences,
  buildChartSeriesConfigItems,
  omitRecordKey,
  resetSeriesViewPreferences,
  runTabularExport,
  seriesViewHasOverrides,
  usePersistedChartPreferences,
  type ChartOverlayOption,
  type MultiTypeSeriesSpec,
  type TableExportPayload,
} from "@delpi/plugin-ui/index";

import { EngineeringSegmentToggle } from "../../../ui/engineeringUi";
import {
  MINUTE,
  SECOND,
  toChartValue,
  type ChartTimeUnit,
} from "./chartUnits";

export type RoutingChartUnitMode = "auto" | "s" | "min";

type RoutingSeriesChartProps = {
  /** Chave de preferências do gráfico (namespace engineering). */
  storageKey: string;
  idPrefix: string;
  /** Linhas categóricas com valores em minutos (`categoria` + dataKeys). */
  data: ReadonlyArray<Record<string, unknown>>;
  /** Séries base (dataKey/nome/fill/plotAs) — valores em minutos. */
  series: ReadonlyArray<MultiTypeSeriesSpec>;
  /** Unidade resolvida automaticamente pela magnitude dos dados. */
  autoUnit: ChartTimeUnit;
  /** dataKey com fill por categoria (ex.: acima do takt). */
  categoryFillKey?: string;
  /** Payload de exportação montado com a unidade efetiva. */
  buildExportPayload: (unit: ChartTimeUnit) => TableExportPayload;
  emptyMessage: string;
};

const UNIT_OPTIONS = [
  { value: "auto", label: "Auto" },
  { value: "s", label: "s" },
  { value: "min", label: "min" },
] as const;

function formatAxisValue(decimals: number) {
  return (value: number): string =>
    !Number.isFinite(value)
      ? "—"
      : value.toLocaleString("pt-BR", { maximumFractionDigits: decimals });
}

export function RoutingSeriesChart({
  storageKey,
  idPrefix,
  data,
  series: baseSeries,
  autoUnit,
  categoryFillKey,
  buildExportPayload,
  emptyMessage,
}: RoutingSeriesChartProps) {
  const { preferences, setPreferences, setChartType } =
    usePersistedChartPreferences({
      storageKey,
      defaults: { chartType: "bar", displayUnit: "auto" },
      allowedChartTypes: CATEGORICAL_TYPES,
    });
  const chartType = preferences.chartType ?? "bar";
  const unitMode = (preferences.displayUnit ?? "auto") as RoutingChartUnitMode;
  const unit =
    unitMode === "s" ? SECOND : unitMode === "min" ? MINUTE : autoUnit;
  const showValueLabels = Boolean(preferences.showValueLabels);
  const formatValue = useMemo(
    () => formatAxisValue(unit.decimalPlaces),
    [unit.decimalPlaces],
  );

  const chartData = useMemo(
    () =>
      data.map((row) => {
        const next: Record<string, unknown> = { ...row };
        for (const spec of baseSeries) {
          const raw = row[spec.dataKey];
          next[spec.dataKey] = toChartValue(
            typeof raw === "number" ? raw : null,
            unit,
          );
        }
        return next;
      }),
    [baseSeries, data, unit],
  );

  const series = useMemo(
    () => applySeriesViewPreferences(baseSeries, preferences),
    [baseSeries, preferences],
  );
  const seriesConfigItems = useMemo(
    () => buildChartSeriesConfigItems(baseSeries, preferences),
    [baseSeries, preferences],
  );

  const overlayOptions = useMemo((): ChartOverlayOption[] => {
    return [
      {
        id: "value-labels",
        label: "Rótulos de valor",
        summaryLabel: "Rótulos",
        checked: showValueLabels,
        onChange: (checked) => setPreferences({ showValueLabels: checked }),
        hint: "Exibe o valor de cada barra/ponto diretamente no gráfico.",
      },
    ];
  }, [setPreferences, showValueLabels]);

  /* Compacto com poucas categorias — sem área vazia gigante. */
  const height = data.length <= 2 ? 220 : 320;
  /* Em horizontal_bar todas as séries viram barras — a cor por categoria
   * (ex.: acima do takt) também pintaria a série de referência. */
  const effectiveFillKey =
    chartType === "horizontal_bar" ? undefined : categoryFillKey;

  if (data.length === 0) {
    return <p className="engineering-routing__muted">{emptyMessage}</p>;
  }

  return (
    <ChartViewShell
      prefix="engineering"
      granularityLabel="Unidade"
      overlaysLabel="Opções"
      seriesColorsLabel="Séries"
      typeToggleLabel="Tipo"
      granularity={
        <EngineeringSegmentToggle
          options={[...UNIT_OPTIONS]}
          value={unitMode}
          onChange={(mode) =>
            setPreferences({ displayUnit: String(mode) })
          }
          size="sm"
          widthMode="content"
          ariaLabel="Unidade de exibição do gráfico"
        />
      }
      typeToggle={
        <ChartTypeSegmentToggle
          family="categorical"
          value={chartType}
          onChange={setChartType}
          idPrefix={`${idPrefix}-type`}
          prefix="engineering"
          categoryCount={data.length}
          portalScopeClassName="portal-engineering"
        />
      }
      exportActions={
        <TabularExportButtons
          onExport={(format) => {
            runTabularExport({
              kind: "table",
              format,
              payload: buildExportPayload(unit),
            });
          }}
        />
      }
      overlays={
        <ChartOverlayOptionsPopover
          idPrefix={`${idPrefix}-overlays`}
          portalScopeClassName="portal-engineering"
          panelTitle="Opções de exibição"
          emptySummaryLabel="Sem opções"
          options={overlayOptions}
        />
      }
      seriesColors={
        <ChartSeriesColorsPopover
          idPrefix={`${idPrefix}-colors`}
          portalScopeClassName="portal-engineering"
          series={seriesConfigItems}
          values={preferences.seriesFills}
          hasOverrides={seriesViewHasOverrides(preferences)}
          summaryLabel="Configurar séries"
          panelTitle="Séries e cores"
          triggerAriaLabel="Configurar séries e cores"
          resetLabel="Redefinir"
          resetSeriesLabel="Redefinir série"
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
        categoryKey="categoria"
        series={series}
        chartType={chartType}
        height={height}
        formatY={formatValue}
        formatTooltipValue={(v) => `${formatValue(v)} ${unit.unit}`}
        showValueLabels={showValueLabels}
        categoryFillKey={effectiveFillKey}
      />
    </ChartViewShell>
  );
}
