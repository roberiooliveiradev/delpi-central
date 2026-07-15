import { DelpiKpiCard } from "@delpi/plugin-ui/index";

import { resolveComunicadoLucideIcon } from "./comunicadoIconView";
import {
  isKpiPartVisible,
  mergeKpiPartsWithOptions,
  type ComunicadoKpiInteraction,
} from "./comunicadoKpiParts";
import type { ComunicadoKpiViewBlock } from "./comunicadoTypes";
import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";
import { applyMetricSelectionToResolved } from "./resolveKpiMetrics";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

type Props = {
  block: ComunicadoKpiViewBlock;
  interactive?: boolean;
  loading?: boolean;
  interaction?: ComunicadoKpiInteraction | null;
};

function KpiTypePlaceholder({
  loading,
  interactive,
  bound,
}: {
  loading?: boolean;
  interactive?: boolean;
  bound?: boolean;
}) {
  const hint = loading
    ? "Carregando dados…"
    : bound
      ? "Fonte sem valor numérico"
      : interactive
        ? "Conecte uma fonte de dados"
        : "Sem dados";
  return (
    <div className="tdp-data-chart tdp-data-chart--typed">
      <span className="tdp-data-chart__type">KPI</span>
      <span className="tdp-data-chart__hint">{hint}</span>
    </div>
  );
}

export function KpiViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
}: Props) {
  const resolved = applyMetricSelectionToResolved(block.resolved, {
    selectedValueFields: block.selectedValueFields,
    valueField: block.valueField,
  });
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
        <KpiTypePlaceholder loading={loading} interactive={interactive} bound={bound} />
      </div>
    );
  }

  const metrics = resolved.kpiMetrics ?? [];
  const hasMulti = metrics.length > 1;
  const hasValue =
    hasMulti || (resolved.kpi?.value != null && resolved.kpi.value !== "");
  if (!hasValue) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <KpiTypePlaceholder loading={loading} interactive={interactive} bound />
      </div>
    );
  }

  // Parts são a fonte de verdade (paridade editor ↔ prévia ↔ apresentação).
  const mergedParts = mergeKpiPartsWithOptions(block.kpiParts, block.kpiOptions);
  const kpiInteraction = interactive ? interaction : null;

  const renderCard = (metricResolved = resolved) => {
    const presentation = resolveKpiViewPresentation(metricResolved, block.kpiOptions);
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
        fill
      />
    );
  };

  if (hasMulti) {
    return (
      <div className="tdp-data-block tdp-data-block--kpi tdp-kpi-view tdp-kpi-view--multi">
        {metrics.map((metric) => (
          <div key={metric.field} className="tdp-kpi-view__cell">
            {renderCard({
              ...resolved,
              kpi: { value: metric.value, label: metric.label },
              label: metric.label,
            })}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="tdp-data-block tdp-data-block--kpi tdp-kpi-view">
      {renderCard()}
    </div>
  );
}
