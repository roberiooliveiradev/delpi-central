import { DelpiKpiCard } from "@delpi/plugin-ui/index";

import { resolveComunicadoLucideIcon } from "./comunicadoIconView";
import type { ComunicadoKpiInteraction } from "./comunicadoKpiParts";
import type { ComunicadoKpiViewBlock } from "./comunicadoTypes";
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
  const resolved = block.resolved;
  const bound = Boolean(block.dataSourceId?.trim());

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
        <KpiTypePlaceholder loading={loading} interactive={interactive} bound={bound} />
      </div>
    );
  }

  const presentation = resolveKpiViewPresentation(resolved, block.kpiOptions);
  const hasValue = resolved.kpi?.value != null && resolved.kpi.value !== "";
  if (!hasValue) {
    return (
      <div className={`tdp-data-block tdp-data-block--placeholder${loading ? " tdp-data-block--loading" : ""}`}>
        <KpiTypePlaceholder loading={loading} interactive={interactive} bound />
      </div>
    );
  }

  const Icon = presentation.iconName ? resolveComunicadoLucideIcon(presentation.iconName) : null;
  const showIcon = presentation.showIcon && Icon;
  const kpiInteraction = interactive ? interaction : null;

  return (
    <div className="tdp-data-block tdp-data-block--kpi tdp-kpi-view">
      <DelpiKpiCard
        label={presentation.label}
        value={presentation.valueText}
        hint={presentation.hint}
        tone={presentation.tone}
        valueColor={presentation.valueColor}
        backgroundColor={presentation.backgroundColor}
        icon={showIcon && Icon ? <Icon aria-hidden size={22} strokeWidth={2} /> : undefined}
        kpiOptions={block.kpiOptions}
        kpiParts={block.kpiParts}
        interaction={kpiInteraction}
      />
    </div>
  );
}
