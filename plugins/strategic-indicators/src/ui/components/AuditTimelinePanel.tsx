import type { StrategicIndicatorsSettingsAuditItem } from "../../data/types/settingsAudit";

type AuditTimelinePanelProps = {
  items: StrategicIndicatorsSettingsAuditItem[];
  loading: boolean;
  error: string | null;
  onReload: () => void;
};

export function AuditTimelinePanel({
  items,
  loading,
  error,
  onReload,
}: AuditTimelinePanelProps) {
  if (loading) {
    return <div className="si-audit-panel">Carregando auditoria...</div>;
  }

  if (error) {
    return (
      <div className="si-audit-panel si-audit-panel--error">
        <div>{error}</div>
        <button
          type="button"
          className="si-audit-panel__button"
          onClick={onReload}
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="si-audit-panel">
        Nenhum evento de auditoria encontrado até o momento.
      </div>
    );
  }

  return (
    <section className="si-audit-panel">
      <div className="si-audit-panel__list">
        {items.map((item) => {
          const summary = buildAuditSummary(item);

          return (
            <article key={item.id} className="si-audit-item">
              <div className="si-audit-item__top">
                <strong className="si-audit-item__entity">{item.entity_key}</strong>
                <span className="si-audit-item__event">{item.event_type}</span>
              </div>

              <div className="si-audit-item__meta">
                <span>
                  Alterado por: {item.changed_by_email || item.changed_by_user_id || "não identificado"}
                </span>
                <span>
                  Em: {new Date(item.created_at).toLocaleString("pt-BR")}
                </span>
              </div>

              <div className="si-audit-item__summary">
                <span className="si-audit-item__summary-label">Resumo da alteração</span>
                <p className="si-audit-item__summary-text">{summary}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function buildAuditSummary(item: StrategicIndicatorsSettingsAuditItem): string {
  const beforeCount = extractItemsCount(item.payload_before);
  const afterCount = extractItemsCount(item.payload_after);

  if (beforeCount === null && afterCount === null) {
    return "Alteração registrada sem resumo estruturado.";
  }

  if (beforeCount === afterCount) {
    return `Bloco manteve ${afterCount ?? 0} item(ns), com atualização de conteúdo.`;
  }

  return `Bloco mudou de ${beforeCount ?? 0} para ${afterCount ?? 0} item(ns).`;
}

function extractItemsCount(payload: Record<string, unknown> | null): number | null {
  if (!payload) return null;

  const items = payload["items"];
  if (!Array.isArray(items)) return null;

  return items.length;
}