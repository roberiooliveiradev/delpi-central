import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import type { TimelineItemModel, TimelineTone } from "@delpi/plugin-ui/index";
import { FilePenLine, PlusCircle } from "lucide-react";

import { fetchLmpNonconformityHistory } from "../api/lmpNonconformityApi";
import { SectionCard } from "./ncUi";
import { NcTimeline } from "./NcTimeline";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  LmpNcHistoryChangeField,
  LmpNcHistoryEvent,
} from "../types/lmpNonconformity";
import { lmpNcStatusLabel } from "../types/lmpNonconformity";

const NC_HELP = LMPS_HELP_TOOLTIPS.nonconformities;

type Props = {
  recordId: string;
  reloadKey?: number;
};

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("pt-BR");
}

function formatChangeValue(field: string, value: unknown): string {
  if (value == null || value === "") return "—";
  if (field === "status" && typeof value === "string") {
    return lmpNcStatusLabel(value);
  }
  if (field === "problem_tags" && Array.isArray(value)) {
    return value.length ? value.map(String).join(", ") : "—";
  }
  if (field === "products" && Array.isArray(value)) {
    if (!value.length) return "—";
    return value
      .map((item) => {
        if (!item || typeof item !== "object") return String(item);
        const row = item as { product_code?: string; product_description?: string };
        const code = row.product_code?.trim() || "?";
        const desc = row.product_description?.trim();
        return desc ? `${code} (${desc})` : code;
      })
      .join(", ");
  }
  return String(value);
}

function formatFieldDiff(change: LmpNcHistoryChangeField): string {
  const oldText = formatChangeValue(change.field, change.old);
  const newText = formatChangeValue(change.field, change.new);
  if (change.old == null || change.old === "") {
    return `${change.label}: ${newText}`;
  }
  return `${change.label}: ${oldText} → ${newText}`;
}

function eventTitle(event: LmpNcHistoryEvent): string {
  if (event.event_type === "created") return "Não conformidade criada";
  return "Informações atualizadas";
}

function eventTone(eventType: string): TimelineTone {
  return eventType === "created" ? "success" : "info";
}

function eventMarker(eventType: string) {
  if (eventType === "created") {
    return <PlusCircle size={12} strokeWidth={2.25} />;
  }
  return <FilePenLine size={12} strokeWidth={2.25} />;
}

function actorMeta(event: LmpNcHistoryEvent): string {
  const name = event.actor_name?.trim();
  const email = event.actor_email?.trim();
  const userId = event.actor_user_id?.trim();
  const parts: string[] = [];
  if (name) parts.push(name);
  if (email) parts.push(email);
  if (userId && userId !== "unknown") parts.push(`id ${userId}`);
  return parts.join(" · ") || "Usuário desconhecido";
}

function eventDetail(event: LmpNcHistoryEvent): ReactNode {
  const fields = event.changes?.fields ?? [];
  if (!fields.length) {
    return event.event_type === "created" ? "Registro inicial." : undefined;
  }
  return (
    <div className="lmps-nc-history-diffs">
      {fields.map((field) => (
        <div key={field.field}>{formatFieldDiff(field)}</div>
      ))}
    </div>
  );
}

function toTimelineItem(event: LmpNcHistoryEvent): TimelineItemModel {
  return {
    id: event.id,
    title: eventTitle(event),
    occurredAt: event.created_at,
    timeLabel: formatDateTime(event.created_at),
    detail: eventDetail(event),
    meta: actorMeta(event),
    tone: eventTone(event.event_type),
    marker: eventMarker(event.event_type),
  };
}

export function NcChangeHistory({ recordId, reloadKey = 0 }: Props) {
  const [items, setItems] = useState<LmpNcHistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformityHistory(recordId);
      setItems(data.items ?? []);
    } catch (err) {
      setItems([]);
      setError(err instanceof Error ? err.message : "Erro ao carregar histórico.");
    } finally {
      setLoading(false);
    }
  }, [recordId]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  const timelineItems = useMemo(() => items.map(toTimelineItem), [items]);

  return (
    <SectionCard title="Histórico de alterações" hint={NC_HELP.form.sectionHistory}>
      {error ? (
        <div className="lmps-refreshing-banner" role="alert">
          {error}
        </div>
      ) : null}
      <NcTimeline
        items={timelineItems}
        loading={loading}
        emptyMessage="Nenhuma alteração registrada ainda."
        aria-label="Histórico de alterações da não conformidade"
      />
    </SectionCard>
  );
}
