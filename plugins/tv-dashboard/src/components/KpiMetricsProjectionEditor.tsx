import { FormSelectControl, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  VIEW_AGGREGATION_OPTIONS,
  type KpiMetricProjection,
  type KpiViewProjection,
  type ViewAggregation,
} from "@delpi/tv-dashboard-presentation";

import { KpiColorRulesEditor } from "./KpiColorRulesEditor";
import type { ValueFieldOption } from "./ValueFieldsMultiSelect";

type Props = {
  idPrefix: string;
  options: ValueFieldOption[];
  kpiProjection?: KpiViewProjection | null;
  onChange: (next: KpiViewProjection | undefined) => void;
  compact?: boolean;
};

function resolveMetrics(
  options: ValueFieldOption[],
  projection?: KpiViewProjection | null,
): KpiMetricProjection[] {
  if (projection?.metrics?.length) {
    const byField = new Map(projection.metrics.map((metric) => [metric.field, metric]));
    const ordered = projection.metrics.filter((metric) =>
      options.some((opt) => opt.field === metric.field),
    );
    for (const opt of options) {
      if (!byField.has(opt.field)) {
        ordered.push({ field: opt.field, visible: true, aggregation: "first" });
      }
    }
    return ordered;
  }
  return options.map((opt) => ({
    field: opt.field,
    label: opt.label,
    visible: true,
    aggregation: "first" as const,
  }));
}

/**
 * Configuração segregada por métrica: visível, agregação e formato.
 */
export function KpiMetricsProjectionEditor({
  idPrefix,
  options,
  kpiProjection,
  onChange,
  compact = false,
}: Props) {
  if (options.length === 0) return null;

  const metrics = resolveMetrics(options, kpiProjection);
  const visibleCount = metrics.filter((metric) => metric.visible !== false).length;

  const persist = (nextMetrics: KpiMetricProjection[]) => {
    const catalog = new Set(options.map((opt) => opt.field));
    const cleaned = nextMetrics.filter((metric) => catalog.has(metric.field));
    const allVisible =
      cleaned.length === options.length && cleaned.every((metric) => metric.visible !== false);
    const allFirst =
      allVisible &&
      cleaned.every(
        (metric) =>
          (metric.aggregation ?? "first") === "first" &&
          !metric.format &&
          !metric.colorRules?.length &&
          !metric.label,
      );
    if (allFirst) {
      onChange(undefined);
      return;
    }
    onChange({ metrics: cleaned });
  };

  const patchMetric = (field: string, patch: Partial<KpiMetricProjection>) => {
    persist(
      metrics.map((metric) => (metric.field === field ? { ...metric, ...patch } : metric)),
    );
  };

  return (
    <div
      className={
        compact
          ? "td-deck-inspector__value-fields td-deck-inspector__value-fields--compact"
          : "td-deck-inspector__value-fields"
      }
      role="group"
      aria-label="Métricas do KPI"
    >
      <p className="td-deck-inspector__hint">
        {visibleCount} de {options.length} métricas — agregação e formato por coluna
      </p>
      {metrics.map((metric) => {
        const label = options.find((opt) => opt.field === metric.field)?.label || metric.field;
        const visible = metric.visible !== false;
        return (
          <div key={metric.field} className="td-deck-inspector__kpi-metric">
            <NativeCheckboxControl
              id={`${idPrefix}-${metric.field}-vis`}
              className="td-deck-inspector__checkbox"
              checked={visible}
              label={label}
              onChange={(checked) => patchMetric(metric.field, { visible: checked })}
            />
            {visible ? (
              <div className="td-deck-inspector__kpi-metric-controls">
                <FormSelectControl
                  id={`${idPrefix}-${metric.field}-agg`}
                  className={compact ? "delpi-ui-select--compact" : undefined}
                  ariaLabel={`Agregação de ${label}`}
                  value={metric.aggregation ?? "first"}
                  onChange={(value) =>
                    patchMetric(metric.field, { aggregation: value as ViewAggregation })
                  }
                  options={VIEW_AGGREGATION_OPTIONS.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                />
                <FormSelectControl
                  id={`${idPrefix}-${metric.field}-fmt`}
                  className={compact ? "delpi-ui-select--compact" : undefined}
                  ariaLabel={`Formato de ${label}`}
                  value={metric.format ?? "raw"}
                  onChange={(value) =>
                    patchMetric(metric.field, {
                      format: value as KpiMetricProjection["format"],
                    })
                  }
                  options={[
                    { value: "raw", label: "Como veio" },
                    { value: "number", label: "Número" },
                    { value: "percent", label: "Percentual" },
                    { value: "compact", label: "Compacto" },
                  ]}
                />
                <NativeTextControl
                  id={`${idPrefix}-${metric.field}-label`}
                  className={compact ? "delpi-ui-native-control--compact" : undefined}
                  placeholder="Rótulo opcional"
                  value={metric.label ?? ""}
                  onChange={(value) =>
                    patchMetric(metric.field, { label: value.trim() || undefined })
                  }
                />
                <div className="td-deck-inspector__kpi-metric-rules">
                  <p className="td-deck-inspector__hint">Cores condicionais desta métrica</p>
                  <KpiColorRulesEditor
                    idPrefix={`${idPrefix}-${metric.field}-rules`}
                    rules={metric.colorRules ?? []}
                    compact={compact}
                    onChange={(colorRules) => patchMetric(metric.field, { colorRules })}
                  />
                </div>
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
