import { chartTypeLabel, chartTypeToLegacyDisplayMode } from "./comunicadoChartView";
import type { ComunicadoChartViewBlock, ComunicadoDataResolved } from "./comunicadoTypes";
import { TvDataBarChartWidget, TvDataLineChartWidget } from "./tvDataChartWidgets";
import { resolveChartType } from "./tvDataPresentation";

type Props = {
  block: ComunicadoChartViewBlock;
  interactive?: boolean;
  loading?: boolean;
};

function ChartTypePlaceholder({
  chartType,
  label,
  loading,
  interactive,
}: {
  chartType: string;
  label: string;
  loading?: boolean;
  interactive?: boolean;
}) {
  return (
    <div className="tdp-data-chart tdp-data-chart--typed">
      <span className="tdp-data-chart__type">{chartTypeLabel(chartType as ComunicadoChartViewBlock["chartType"])}</span>
      <span className="tdp-data-chart__hint">
        {loading ? "Carregando dados…" : interactive ? "Conecte uma fonte de dados" : label}
      </span>
    </div>
  );
}

export function ChartViewBlockView({ block, interactive = false, loading = false }: Props) {
  const resolved = block.resolved;
  const label = resolved?.label ?? chartTypeLabel(block.chartType);

  if (resolved?.error) {
    return (
      <div className="tdp-data-block tdp-data-block--error">
        <span>{String(resolved.error)}</span>
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
        />
      </div>
    );
  }

  const displayMode = chartTypeToLegacyDisplayMode(block.chartType);
  const chartType = resolveChartType(displayMode, resolved);
  const points = resolved.chart?.points ?? [];

  if (points.length === 0 && !resolved.kpi?.value) {
    return (
      <div className="tdp-data-block tdp-data-block--chart">
        <ChartTypePlaceholder chartType={block.chartType} label={label} loading={loading} interactive={interactive} />
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

  return (
    <div className={`tdp-data-block tdp-data-block--chart tdp-data-block--chart-${chartType}`}>
      {chartType === "bar" ? (
        <TvDataBarChartWidget resolved={resolved} chartOptions={block.chartOptions} />
      ) : (
        <TvDataLineChartWidget resolved={resolved} chartOptions={block.chartOptions} />
      )}
    </div>
  );
}

export type { ComunicadoDataResolved };
