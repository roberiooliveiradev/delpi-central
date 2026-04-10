import { useMemo } from "react";
import type {
  StrategicIndicatorsAuditEntityKey,
  StrategicIndicatorsSettingsAuditItem,
} from "../../data/types/settingsAudit";

type AuditLatestByEntityPanelProps = {
  items: StrategicIndicatorsSettingsAuditItem[];
  activeEntityKey: "all" | StrategicIndicatorsAuditEntityKey;
  onSelectEntityKey: (
    value: "all" | StrategicIndicatorsAuditEntityKey,
  ) => void;
};

type EntitySummary = {
  entityKey: StrategicIndicatorsAuditEntityKey;
  entityLabel: string;
  actor: string;
  createdAt: string;
  eventType: string;
};

const ENTITY_ORDER: StrategicIndicatorsAuditEntityKey[] = [
  "departments",
  "department_indicators",
  "indicator_goals",
  "parameters.global",
  "governance.notes",
  "weights.departments",
  "goals.summary",
];

export function AuditLatestByEntityPanel({
  items,
  activeEntityKey,
  onSelectEntityKey,
}: AuditLatestByEntityPanelProps) {
  const summaries = useMemo(() => {
    const grouped = new Map<string, StrategicIndicatorsSettingsAuditItem>();

    for (const item of items) {
      const current = grouped.get(item.entity_key);

      if (!current) {
        grouped.set(item.entity_key, item);
        continue;
      }

      const currentDate = new Date(current.created_at).getTime();
      const candidateDate = new Date(item.created_at).getTime();

      if (candidateDate > currentDate) {
        grouped.set(item.entity_key, item);
      }
    }

    const result: EntitySummary[] = [];

    for (const entityKey of ENTITY_ORDER) {
      const item = grouped.get(entityKey);
      if (!item) continue;

      result.push({
        entityKey,
        entityLabel: humanizeEntityKey(entityKey),
        actor:
          item.changed_by_email ||
          item.changed_by_user_id ||
          "não identificado",
        createdAt: item.created_at,
        eventType: humanizeEventType(item.event_type),
      });
    }

    return result;
  }, [items]);

  if (!summaries.length) {
    return (
      <div className="si-audit-latest">
        Nenhuma alteração recente encontrada para os blocos auditados.
      </div>
    );
  }

  return (
    <section className="si-audit-latest">
      <div className="si-audit-latest__grid">
        {summaries.map((item) => {
          const isActive = activeEntityKey === item.entityKey;

          return (
            <button
              key={item.entityKey}
              type="button"
              className={`si-audit-latest__card ${
                isActive ? "si-audit-latest__card--active" : ""
              }`}
              onClick={() => onSelectEntityKey(item.entityKey)}
            >
              <span className="si-audit-latest__label">{item.entityLabel}</span>
              <strong className="si-audit-latest__value">{item.eventType}</strong>
              <p className="si-audit-latest__meta">
                Última alteração por <strong>{item.actor}</strong>
              </p>
              <p className="si-audit-latest__date">
                {new Date(item.createdAt).toLocaleString("pt-BR")}
              </p>
              <span className="si-audit-latest__hint">
                {isActive ? "Filtro ativo" : "Clique para focar"}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function humanizeEntityKey(entityKey: string): string {
  const map: Record<string, string> = {
    "departments": "Departamentos",
    "department_indicators": "Indicadores estruturais",
    "indicator_goals": "Metas anuais",
    "parameters.global": "Parâmetros globais",
    "governance.notes": "Governança",
    "weights.departments": "Pesos por departamento (legado)",
    "goals.summary": "Metas resumidas (legado)",
  };

  return map[entityKey] ?? entityKey;
}

function humanizeEventType(eventType: string): string {
  const map: Record<string, string> = {
    "settings.updated": "Atualização",
  };

  return map[eventType] ?? eventType;
}