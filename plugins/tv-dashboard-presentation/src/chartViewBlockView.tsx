import {
  chartTypeHasBasicRender,
  chartTypeLabel,
  toSeriesChartKind,
} from "./comunicadoChartView";
import type { ComunicadoChartInteraction } from "./comunicadoChartParts";
import { resolveChartDisplayOptions } from "./comunicadoChartOptions";
import type { ComunicadoChartViewBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import {
  DataBlockRefreshBadge,
  withDataBlockLoadingClass,
} from "./dataBlockRefreshChrome";
import { GaugeChartView } from "./GaugeChartView";
import { resolveGaugeChartModel } from "./gaugeChartModel";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import {
  mergeChartViewFilterParams,
  shouldApplyExcludeWeekends,
} from "./chartWeekendFilter";
import { applyViewProjection } from "./viewProjection";
import { TvDataSeriesChartWidget } from "./tvDataChartWidgets";

type Props = {
  block: ComunicadoChartViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoChartInteraction | null;
  /** Playlist + slide + fonte (live). Enrichment também carimba `resolved.viewFilterParams`. */
  filterParams?: Record<string, unknown> | null;
};

function ChartTypePlaceholder({
  chartType,
  label,
  loading,
  interactive,
  bound,
  emptyData,
}: {
  chartType: string;
  label: string;
  loading?: boolean;
  interactive?: boolean;
  bound?: boolean;
  /** Fonte resolveu, mas a coluna/encoding escolhida não tem pontos. */
  emptyData?: boolean;
}) {
  const hint = loading
    ? "Carregando dados…"
    : bound && emptyData
      ? "Sem dados"
      : bound
        ? chartType === "gauge"
          ? "Sem valor — escolha a medida na conexão do visual"
          : chartType === "pie" || chartType === "doughnut"
            ? "Sem fatias — escolha a categoria (ex.: Tipo) na conexão do visual"
            : "Sem série ou valor — escolha campos na conexão do visual"
        : interactive
          ? "Conecte uma fonte de dados"
          : label;
  return (
    <div className="tdp-data-chart tdp-data-chart--typed">
      <span className="tdp-data-chart__type">{chartTypeLabel(chartType as ComunicadoChartViewBlock["chartType"])}</span>
      <span className="tdp-data-chart__hint">{hint}</span>
    </div>
  );
}

export function ChartViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
  filterParams = null,
}: Props) {
  const viewFilters = mergeChartViewFilterParams([
    block.resolved?.viewFilterParams,
    filterParams,
  ]);
  const resolved = applyViewProjection(block.resolved, {
    chartProjection: block.chartProjection,
    chartType: block.chartType,
    excludeWeekends: shouldApplyExcludeWeekends(viewFilters),
  });
  const label = resolved?.label ?? chartTypeLabel(block.chartType);
  const chartInteraction = interactive ? interaction : null;
  const bound = Boolean(block.dataSourceId?.trim());

  const errorText = resolveDataBlockErrorText(resolved);
  if (errorText) {
    return (
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--error",
          loading,
        )}
      >
        <span>{errorText}</span>
        <DataBlockRefreshBadge loading={loading} />
      </div>
    );
  }

  if (!resolved) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <ChartTypePlaceholder
          chartType={block.chartType}
          label={label}
          loading={loading}
          interactive={interactive}
          bound={bound}
        />
      </div>
    );
  }

  if (block.chartType === "gauge") {
    const displayOptions = resolveChartDisplayOptions(block.chartOptions, resolved);
    const model = resolveGaugeChartModel({
      block,
      resolved,
      options: displayOptions,
    });
    if (model.value == null) {
      return (
        <div className="tdp-data-block tdp-data-block--chart">
          <ChartTypePlaceholder
            chartType={block.chartType}
            label={label}
            loading={loading}
            interactive={interactive}
            bound
            emptyData
          />
        </div>
      );
    }
    return (
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--chart tdp-data-block--chart-gauge",
          loading,
        )}
      >
        <DataBlockRefreshBadge loading={loading} />
        <GaugeChartView
          model={model}
          options={displayOptions}
          chartParts={block.chartParts}
          interaction={chartInteraction}
        />
      </div>
    );
  }

  const points = resolved.chart?.points ?? [];
  const hasFinitePoints =
    points.some((point) => {
      const n = typeof point.value === "number" ? point.value : Number(point.value);
      return Number.isFinite(n);
    }) ||
    (resolved.chart?.series ?? []).some((entry) =>
      (entry.points ?? []).some((point) => {
        const n = typeof point.value === "number" ? point.value : Number(point.value);
        return Number.isFinite(n);
      }),
    );

  // Encoding vazio: nunca cair no card KPI com buckets_count / cobertura do envelope.
  // Também: pontos só com null (linhas sem medida) → Sem dados, não barra inventada.
  if (points.length === 0 || !hasFinitePoints) {
    return (
      <div className="tdp-data-block tdp-data-block--chart">
        <ChartTypePlaceholder
          chartType={block.chartType}
          label={label}
          loading={loading}
          interactive={interactive}
          bound
          emptyData
        />
      </div>
    );
  }

  if (!chartTypeHasBasicRender(block.chartType) || toSeriesChartKind(block.chartType) == null) {
    return (
      <div className="tdp-data-block tdp-data-block--chart">
        <ChartTypePlaceholder
          chartType={block.chartType}
          label={`${chartTypeLabel(block.chartType)} — em breve`}
          loading={loading}
          interactive={interactive}
        />
      </div>
    );
  }

  const kind = toSeriesChartKind(block.chartType)!;

  return (
    <div
      className={withDataBlockLoadingClass(
        `tdp-data-block tdp-data-block--chart tdp-data-block--chart-${kind}`,
        loading,
      )}
    >
      <DataBlockRefreshBadge loading={loading} />
      <TvDataSeriesChartWidget
        resolved={resolved}
        chartOptions={block.chartOptions}
        chartParts={block.chartParts}
        interaction={chartInteraction}
        chartType={block.chartType}
      />
    </div>
  );
}

export type { ComunicadoDataResolved };
