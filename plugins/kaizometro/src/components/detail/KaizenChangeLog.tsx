import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CircleAlert,
  FilePenLine,
  PlusCircle,
  Sparkles,
  Trash2,
} from "lucide-react";
import type { TimelineItemModel, TimelineTone } from "@delpi/plugin-ui/index";

import { fetchKaizenAuditLog, fetchKaizenHistory } from "../../api/kaizenApi";
import type {
  KaizenAuditEntry,
  KaizenHistoryEvent,
  KaizenRevision,
} from "../../types/kaizen";
import { statusLabel } from "../../utils/labels";
import { Timeline } from "../data";
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

function historyTone(eventType: string): TimelineTone {
  if (eventType.endsWith("_deleted") || eventType === "kaizen_deleted") return "danger";
  if (eventType === "status_changed" || eventType === "kaizen_corrected") return "warning";
  if (
    eventType === "kaizen_created" ||
    eventType === "version_created" ||
    eventType === "version_implemented" ||
    eventType === "improvement_added"
  ) {
    return "success";
  }
  return "info";
}

function historyMarker(eventType: string) {
  if (eventType.endsWith("_deleted") || eventType === "kaizen_deleted") {
    return <Trash2 size={12} strokeWidth={2.25} />;
  }
  if (eventType === "status_changed" || eventType === "kaizen_corrected" || eventType === "kaizen_updated") {
    return <FilePenLine size={12} strokeWidth={2.25} />;
  }
  if (eventType === "improvement_added") {
    return <Sparkles size={12} strokeWidth={2.25} />;
  }
  if (
    eventType === "kaizen_created" ||
    eventType === "version_created" ||
    eventType === "version_implemented"
  ) {
    return <PlusCircle size={12} strokeWidth={2.25} />;
  }
  return <CircleAlert size={12} strokeWidth={2.25} />;
}

function toHistoryTimelineItem(event: KaizenHistoryEvent): TimelineItemModel {
  return {
    id: event.id,
    title: eventLabel(event.event_type),
    occurredAt: event.created_at,
    timeLabel: formatDateTime(event.created_at),
    detail: historyDescription(event) ?? undefined,
    meta: event.created_by_name || event.created_by_user_id,
    tone: historyTone(event.event_type),
    marker: historyMarker(event.event_type),
  };
}

type Props = {
  kaizenId: string;
  revisions: KaizenRevision[];
  reloadKey: number;
};

export function KaizenChangeLog({ kaizenId, revisions, reloadKey }: Props) {
  const [history, setHistory] = useState<KaizenHistoryEvent[]>([]);
  const [audit, setAudit] = useState<KaizenAuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [hist, aud] = await Promise.all([
        fetchKaizenHistory(kaizenId).catch(() => [] as KaizenHistoryEvent[]),
        fetchKaizenAuditLog(kaizenId).catch(() => [] as KaizenAuditEntry[]),
      ]);
      setHistory(hist);
      setAudit(aud);
    } finally {
      setLoading(false);
    }
  }, [kaizenId]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  const historyItems = useMemo(() => history.map(toHistoryTimelineItem), [history]);

  return (
    <div className="kz-changelog">
      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Linha do tempo</h3>
        <Timeline
          items={historyItems}
          loading={loading}
          emptyMessage="Nenhum evento registrado."
          aria-label="Linha do tempo do kaizen"
        />
      </div>

      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Versões e mudanças</h3>
        <KaizenRevisionTimeline revisions={revisions} />
      </div>

      <div className="kz-changelog__block">
        <h3 className="kz-changelog__subtitle">Auditoria (governança)</h3>
        {loading ? (
          <EmptyHint>Carregando…</EmptyHint>
        ) : audit.length === 0 ? (
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
