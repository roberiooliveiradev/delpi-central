import { useMemo } from "react";
import type {
  StrategicIndicatorsAuditEntityKey,
  StrategicIndicatorsSettingsAuditItem,
} from "../../data/types/settingsAudit";
import "./AuditSummaryPanel.css";

type AuditSummaryPanelProps = {
  items: StrategicIndicatorsSettingsAuditItem[];
  activeEntityKey: "all" | StrategicIndicatorsAuditEntityKey;
  onSelectEntityKey: (
    value: "all" | StrategicIndicatorsAuditEntityKey,
  ) => void;
};

export function AuditSummaryPanel({
  items,
  activeEntityKey,
  onSelectEntityKey,
}: AuditSummaryPanelProps) {
  const summary = useMemo(() => {
    const counts = {
      total: items.length,
      departments: 0,
      departmentIndicators: 0,
      indicatorGoals: 0,
      parameters: 0,
      governance: 0,
      legacyWeights: 0,
      legacyGoals: 0,
    };

    for (const item of items) {
      if (item.entity_key === "departments") counts.departments += 1;
      if (item.entity_key === "department_indicators") counts.departmentIndicators += 1;
      if (item.entity_key === "indicator_goals") counts.indicatorGoals += 1;
      if (item.entity_key === "parameters.global") counts.parameters += 1;
      if (item.entity_key === "governance.notes") counts.governance += 1;
      if (item.entity_key === "weights.departments") counts.legacyWeights += 1;
      if (item.entity_key === "goals.summary") counts.legacyGoals += 1;
    }

    return counts;
  }, [items]);

  const cards = [
    { key: "all" as const, label: "Eventos totais", value: summary.total },
    { key: "departments" as const, label: "Departamentos", value: summary.departments },
    {
      key: "department_indicators" as const,
      label: "Indicadores estruturais",
      value: summary.departmentIndicators,
    },
    {
      key: "indicator_goals" as const,
      label: "Metas anuais",
      value: summary.indicatorGoals,
    },
    {
      key: "parameters.global" as const,
      label: "Parâmetros",
      value: summary.parameters,
    },
    {
      key: "governance.notes" as const,
      label: "Governança",
      value: summary.governance,
    },
    {
      key: "weights.departments" as const,
      label: "Pesos (legado)",
      value: summary.legacyWeights,
    },
    {
      key: "goals.summary" as const,
      label: "Metas resumidas (legado)",
      value: summary.legacyGoals,
    },
  ];

  return (
    <section className="si-audit-summary">
      {cards.map((card) => {
        const isActive = activeEntityKey === card.key;

        return (
          <button
            key={card.key}
            type="button"
            className={`si-audit-summary__card ${
              isActive ? "si-audit-summary__card--active" : ""
            }`}
            onClick={() => onSelectEntityKey(card.key)}
          >
            <span className="si-audit-summary__label">{card.label}</span>
            <strong className="si-audit-summary__value">{card.value}</strong>
            <span className="si-audit-summary__hint">
              {isActive ? "Filtro ativo" : "Clique para focar"}
            </span>
          </button>
        );
      })}
    </section>
  );
}