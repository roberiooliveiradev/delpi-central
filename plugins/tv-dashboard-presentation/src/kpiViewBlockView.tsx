import { ConfigurableTable } from "./ConfigurableTable";
import { DelpiKpiCard } from "@delpi/plugin-ui/index";

import { resolveComunicadoLucideIcon } from "./comunicadoIconView";
import {
  isKpiPartVisible,
  mergeKpiPartsWithOptions,
  type ComunicadoKpiInteraction,
} from "./comunicadoKpiParts";
import { resolveTableDisplayOptions } from "./comunicadoTableOptions";
import type { ComunicadoDataResolved, ComunicadoKpiViewBlock } from "./comunicadoTypes";
import {
  DataBlockRefreshBadge,
  withDataBlockLoadingClass,
} from "./dataBlockRefreshChrome";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import { applyViewProjection } from "./viewProjection";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";
import { applyTableViewDisplayLimits } from "./tableViewLimits";
import { resolveTableColumns } from "./tvDataPresentation";

type Props = {
  block: ComunicadoKpiViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoKpiInteraction | null;
};

/**
 * Card Delpi com título/parts + valor «—» / vazio.
 * Substitui o placeholder tipado «KPI / Sem dados» quando há chrome configurado
 * ou fonte ligada (paridade com chart/table empty-with-title).
 */
function EmptyKpiCard({
  block,
  resolved,
  interaction = null,
}: {
  block: ComunicadoKpiViewBlock;
  resolved?: ComunicadoDataResolved;
  interaction?: ComunicadoKpiInteraction | null;
}) {
  const mergedParts = mergeKpiPartsWithOptions(block.kpiParts, block.kpiOptions);
  const presentation = resolveKpiViewPresentation(resolved, block.kpiOptions);
  const iconAllowed = isKpiPartVisible(mergedParts, { kind: "icon" }, presentation.showIcon);
  const Icon =
    iconAllowed && presentation.iconName
      ? resolveComunicadoLucideIcon(presentation.iconName)
      : null;
  return (
    <DelpiKpiCard
      label={presentation.label}
      value={presentation.valueText || "—"}
      hint={presentation.hint}
      tone={presentation.tone}
      valueColor={presentation.valueColor}
      backgroundColor={presentation.backgroundColor}
      icon={Icon ? <Icon aria-hidden strokeWidth={2} /> : undefined}
      kpiOptions={block.kpiOptions}
      kpiParts={block.kpiParts}
      interaction={interaction}
      comparisonText={presentation.comparisonText}
      comparisonTone={presentation.comparisonTone}
      progressPct={presentation.progressPct}
      sparklinePoints={presentation.sparklinePoints}
      variant={presentation.variant ?? block.kpiOptions?.variant ?? null}
      fill
    />
  );
}

export function KpiViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
}: Props) {
  const resolved = applyViewProjection(block.resolved, {
    kpiProjection: block.kpiProjection,
  });
  const kpiInteraction = interactive ? interaction : null;

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
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--kpi tdp-kpi-view",
          loading,
        )}
      >
        <DataBlockRefreshBadge loading={loading} />
        <EmptyKpiCard block={block} interaction={kpiInteraction} />
      </div>
    );
  }

  const metrics = resolved.kpiMetrics ?? [];
  const hasMulti = metrics.length > 1;
  const hasValue =
    hasMulti || (resolved.kpi?.value != null && resolved.kpi.value !== "");
  if (!hasValue) {
    const tableRows = resolved.table?.rows ?? [];
    if (tableRows.length > 0) {
      const allColumns = resolveTableColumns(resolved, tableRows);
      const { rows, columns } = applyTableViewDisplayLimits(tableRows, allColumns, {});
      const tableOptions = resolveTableDisplayOptions(undefined, "grid", resolved);
      return (
        <div className="tdp-data-block tdp-data-block--table">
          <div className="tdp-data-table-wrap">
            <ConfigurableTable columns={columns} rows={rows} options={tableOptions} preset="grid" />
          </div>
        </div>
      );
    }
    return (
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--kpi tdp-kpi-view",
          loading,
        )}
      >
        <DataBlockRefreshBadge loading={loading} />
        <EmptyKpiCard block={block} resolved={resolved} interaction={kpiInteraction} />
      </div>
    );
  }

  // Parts são a fonte de verdade (paridade editor ↔ prévia ↔ apresentação).
  const mergedParts = mergeKpiPartsWithOptions(block.kpiParts, block.kpiOptions);
  const metricProjectionByField = new Map(
    (block.kpiProjection?.metrics ?? []).map((metric) => [metric.field, metric]),
  );

  const renderCard = (metricResolved = resolved, field?: string) => {
    const metricProj = field ? metricProjectionByField.get(field) : undefined;
    const presentation = resolveKpiViewPresentation(metricResolved, block.kpiOptions, metricProj);
    const iconAllowed = isKpiPartVisible(mergedParts, { kind: "icon" }, presentation.showIcon);
    const Icon =
      iconAllowed && presentation.iconName
        ? resolveComunicadoLucideIcon(presentation.iconName)
        : null;
    const showIcon = Boolean(iconAllowed && Icon);
    return (
      <DelpiKpiCard
        label={presentation.label}
        value={presentation.valueText}
        hint={presentation.hint}
        tone={presentation.tone}
        valueColor={presentation.valueColor}
        backgroundColor={presentation.backgroundColor}
        icon={showIcon && Icon ? <Icon aria-hidden strokeWidth={2} /> : undefined}
        kpiOptions={block.kpiOptions}
        kpiParts={block.kpiParts}
        interaction={hasMulti ? null : kpiInteraction}
        comparisonText={presentation.comparisonText}
        comparisonTone={presentation.comparisonTone}
        progressPct={presentation.progressPct}
        sparklinePoints={presentation.sparklinePoints}
        variant={presentation.variant ?? block.kpiOptions?.variant ?? null}
        fill
      />
    );
  };

  if (hasMulti) {
    const selectedMetricField =
      kpiInteraction?.selectedPart?.kind === "metricCard"
        ? kpiInteraction.selectedPart.field
        : null;
    const editingMetricField =
      kpiInteraction?.editingPart?.kind === "metricCard"
        ? kpiInteraction.editingPart.field
        : null;
    return (
      <div
        className={withDataBlockLoadingClass(
          "tdp-data-block tdp-data-block--kpi tdp-kpi-view tdp-kpi-view--multi",
          loading,
        )}
      >
        <DataBlockRefreshBadge loading={loading} />
        {metrics.map((metric) => {
          const metricRef = { kind: "metricCard" as const, field: metric.field };
          const selected = selectedMetricField === metric.field;
          const editing = editingMetricField === metric.field;
          return (
            <div
              key={metric.field}
              className={
                selected
                  ? "tdp-kpi-view__cell tdp-kpi-view__cell--selected"
                  : "tdp-kpi-view__cell"
              }
              data-kpi-part={`metricCard:${metric.field}`}
              aria-selected={selected || undefined}
              onPointerDown={(event) => {
                if (editing || !kpiInteraction?.onPartPointerDown) return;
                event.stopPropagation();
                kpiInteraction.onPartPointerDown(metricRef, event);
              }}
              onDoubleClick={(event) => {
                if (editing || !kpiInteraction?.onPartDoubleClick) return;
                event.stopPropagation();
                event.preventDefault();
                kpiInteraction.onPartDoubleClick(metricRef, event);
              }}
            >
              {editing ? (
                <input
                  className="tdp-kpi-view__label-edit"
                  defaultValue={metric.label}
                  autoFocus
                  aria-label={`Rótulo de ${metric.field}`}
                  onPointerDown={(event) => event.stopPropagation()}
                  onBlur={(event) =>
                    kpiInteraction?.onPartContentCommit?.(metricRef, event.target.value)
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      (event.target as HTMLInputElement).blur();
                    }
                    if (event.key === "Escape") {
                      event.preventDefault();
                      kpiInteraction?.onPartEditCancel?.();
                    }
                  }}
                />
              ) : (
                renderCard(
                  {
                    ...resolved,
                    kpi: {
                      value: metric.value,
                      label: metric.label,
                      ...(typeof metric.displayValue === "string"
                        ? { displayValue: metric.displayValue }
                        : {}),
                    },
                    label: metric.label,
                  },
                  metric.field,
                )
              )}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div
      className={withDataBlockLoadingClass(
        "tdp-data-block tdp-data-block--kpi tdp-kpi-view",
        loading,
      )}
    >
      <DataBlockRefreshBadge loading={loading} />
      {renderCard(resolved, metrics[0]?.field)}
    </div>
  );
}
