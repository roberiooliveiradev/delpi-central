import { useMemo } from "react";
import type {
  StrategicIndicatorsAuditEntityKey,
  StrategicIndicatorsSettingsAuditItem,
} from "../../data/types/settingsAudit";

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
      weights: 0,
      goals: 0,
      parameters: 0,
      governance: 0,
    };

    for (const item of items) {
      if (item.entity_key === "weights.departments") counts.weights += 1;
      if (item.entity_key === "goals.summary") counts.goals += 1;
      if (item.entity_key === "parameters.global") counts.parameters += 1;
      if (item.entity_key === "governance.notes") counts.governance += 1;
    }

    return counts;
  }, [items]);

  const cards = [
    { key: "all" as const, label: "Eventos totais", value: summary.total },
    { key: "weights.departments" as const, label: "Pesos", value: summary.weights },
    { key: "goals.summary" as const, label: "Metas", value: summary.goals },
    { key: "parameters.global" as const, label: "Parâmetros", value: summary.parameters },
    { key: "governance.notes" as const, label: "Governança", value: summary.governance },
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