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

export function KpiViewBlockView({
  block,
  interactive = false,
  loading = false,
  interaction = null,
}: Props) {
  const resolved = block.resolved;

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
        <div className="tdp-kpi-placeholder">
          <span className="tdp-kpi-placeholder__title">KPI</span>
          <span className="tdp-kpi-placeholder__hint">
            {loading ? "Carregando dados…" : interactive ? "Conecte uma fonte de dados" : "Sem dados"}
          </span>
        </div>
      </div>
    );
  }

  const presentation = resolveKpiViewPresentation(resolved, block.kpiOptions);
  const Icon = presentation.iconName ? resolveComunicadoLucideIcon(presentation.iconName) : null;
  const showIcon = presentation.showIcon && Icon;
  const kpiInteraction = interactive ? interaction : null;

  return (
    <div className="tdp-kpi-view">
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
