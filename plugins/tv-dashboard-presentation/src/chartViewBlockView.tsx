import {
  chartTypeHasBasicRender,
  chartTypeLabel,
  toSeriesChartKind,
} from "./comunicadoChartView";
import type { ComunicadoChartInteraction } from "./comunicadoChartParts";
import type { ComunicadoChartViewBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import { applyMetricSelectionToResolved } from "./resolveKpiMetrics";
import { TvDataSeriesChartWidget } from "./tvDataChartWidgets";

type Props = {
  block: ComunicadoChartViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoChartInteraction | null;
};

function ChartTypePlaceholder({
  chartType,
  label,
  loading,
  interactive,
  bound,
}: {
  chartType: string;
  label: string;
  loading?: boolean;
  interactive?: boolean;
  bound?: boolean;
}) {
  const hint = loading
    ? "Carregando dados…"
    : bound
      ? "Fonte sem série ou valor"
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
}: Props) {
  const resolved = applyMetricSelectionToResolved(block.resolved, {
    selectedValueFields: block.selectedValueFields,
    valueField: block.valueField,
  });
  const label = resolved?.label ?? chartTypeLabel(block.chartType);
  const chartInteraction = interactive ? interaction : null;
  const bound = Boolean(block.dataSourceId?.trim());

  const errorText = resolveDataBlockErrorText(resolved);
  if (errorText) {
    return (
      <div className="tdp-data-block tdp-data-block--error">
        <span>{errorText}</span>
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

  const points = resolved.chart?.points ?? [];

  if (points.length === 0 && !resolved.kpi?.value) {
    return (
      <div className="tdp-data-block tdp-data-block--chart">
        <ChartTypePlaceholder
          chartType={block.chartType}
          label={label}
          loading={loading}
          interactive={interactive}
          bound
        />
      </div>
    );
  }

  if (points.length === 0) {
    return (
      <div className="tdp-data-block tdp-data-block--kpi">
        <div className="tdp-data-kpi">
          <span className="tdp-data-kpi__label">{resolved.kpi?.label ?? label}</span>
          <strong className="tdp-data-kpi__value">{String(resolved.kpi?.value ?? "—")}</strong>
        </div>
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
    <div className={`tdp-data-block tdp-data-block--chart tdp-data-block--chart-${kind}`}>
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
