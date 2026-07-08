import { useCallback, useEffect, useState } from "react";

import { fetchKaizenAuditLog, fetchKaizenHistory } from "../../api/kaizenApi";
import type {
  KaizenAuditEntry,
  KaizenHistoryEvent,
  KaizenRevision,
} from "../../types/kaizen";
import { statusLabel } from "../../utils/labels";
import { EmptyHint } from "../ui";
import { KaizenRevisionTimeline } from "./KaizenRevisionTimeline";

const EVENT_LABELS: Record<string, string> = {
  kaizen_created: "Kaizen criado",
  status_changed: "Status alterado",
  kaizen_corrected: "Correção da versão",
  version_created: "Nova versão criada",
  version_updated: "Versão (rascunho) editada",
  version_implemented: "Versão implantada",
  version_deleted: "Versão excluída",
  improvement_added: "Melhoria lançada",
  kaizen_updated: "Dados atualizados",
  kaizen_deleted: "Kaizen excluído",
};

function eventLabel(type: string): string {
  return EVENT_LABELS[type] ?? type;
}

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("pt-BR");
}

function historyDescription(event: KaizenHistoryEvent): string | null {
  if (event.event_type === "status_changed") {
    return `${statusLabel(event.old_value ?? "")} → ${statusLabel(event.new_value ?? "")}`;
  }
  return event.comment || event.new_value || null;
}

type Props = {
  kaizenId: string;
  revisions: KaizenRevision[];
  reloadKey: number;
};

export function KaizenChangeLog({ kaizenId, revisions, reloadKey }: Props) {
  const [history, setHistory] = useState<KaizenHistoryEvent[]>([]);
  const [audit, setAudit] = useState<KaizenAuditEntry[]>([]);

  const load = useCallback(async () => {
    const [hist, aud] = await Promise.all([
      fetchKaizenHistory(kaizenId).catch(() => [] as KaizenHistoryEvent[]),
      fetchKaizenAuditLog(kaizenId).catch(() => [] as KaizenAuditEntry[]),
    ]);
    setHistory(hist);
    setAudit(aud);
  }, [kaizenId]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  return (
    <div className="kz-changelog">
      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Linha do tempo</h3>
        {history.length === 0 ? (
          <EmptyHint>Nenhum evento registrado.</EmptyHint>
        ) : (
          <ol className="kz-history">
            {history.map((event) => {
              const description = historyDescription(event);
              return (
                <li key={event.id} className="kz-history__item">
                  <div className="kz-history__marker" aria-hidden="true" />
                  <div className="kz-history__body">
                    <div className="kz-history__head">
                      <span className="kz-history__title">{eventLabel(event.event_type)}</span>
                      <span className="kz-history__date">{formatDateTime(event.created_at)}</span>
                    </div>
                    {description ? <p className="kz-history__desc">{description}</p> : null}
                    <span className="kz-history__author">
                      {event.created_by_name || event.created_by_user_id}
                    </span>
                  </div>
                </li>
              );
            })}
          </ol>
        )}
      </div>

      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Versões e mudanças</h3>
        <KaizenRevisionTimeline revisions={revisions} />
      </div>

      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Auditoria (governança)</h3>
        {audit.length === 0 ? (
          <EmptyHint>Sem eventos de governança.</EmptyHint>
        ) : (
          <ul className="kz-audit">
            {audit.map((entry) => (
              <li key={entry.id} className="kz-audit__item">
                <span className="kz-audit__event">{eventLabel(entry.event_type)}</span>
                <span className="kz-audit__actor">{entry.actor_name || entry.actor_user_id}</span>
                <span className="kz-audit__date">{formatDateTime(entry.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
