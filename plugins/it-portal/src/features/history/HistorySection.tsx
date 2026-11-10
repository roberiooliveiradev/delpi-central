import { useQuery, type QueryKey } from "@tanstack/react-query";

import type { ActionStatus, HistoryEntityType, HistoryEvent, HostingRuntime } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpSectionCard } from "../../app/itPortalUi";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import {
  ACTION_FIELD_LABELS,
  ACTION_STATUS_LABELS,
  DATABASE_FIELD_LABELS,
  HISTORY_EVENT_LABELS,
  HOSTING_RUNTIME_LABELS,
  SERVER_FIELD_LABELS,
  SERVICE_FIELD_LABELS,
} from "../../content/labels";

type Ref = { code?: string; name?: string } | undefined;

const FIELD_LABELS_BY_ENTITY: Partial<Record<HistoryEntityType, Record<string, string>>> = {
  server: SERVER_FIELD_LABELS,
  action_plan: ACTION_FIELD_LABELS,
  service: SERVICE_FIELD_LABELS,
  database_instance: DATABASE_FIELD_LABELS,
};

function refLabel(ref: Ref): string {
  if (!ref) return "—";
  return [ref.code, ref.name].filter(Boolean).join(" · ") || "—";
}

export function describeHistoryChange(event: HistoryEvent): string | null {
  const changes = event.changes ?? {};
  if (event.event_type === "action_plan_status_changed") {
    const status = changes.status as { from?: string; to?: string } | undefined;
    const label = (value?: string) => ACTION_STATUS_LABELS[value as ActionStatus] ?? value ?? "—";
    return status ? `De ${label(status.from)} para ${label(status.to)}` : null;
  }
  if (event.entity_type === "service_hosting") {
    const runtime = HOSTING_RUNTIME_LABELS[changes.runtime as HostingRuntime] ?? "";
    const suffix = runtime ? ` (${runtime})` : "";
    return `${refLabel(changes.service as Ref)} em ${refLabel(changes.server as Ref)}${suffix}`;
  }
  if (event.entity_type === "database_consumer") {
    return `${refLabel(changes.service as Ref)} usa ${refLabel(changes.database as Ref)}`;
  }
  const fields = Object.keys(changes);
  if (event.event_type.endsWith("_updated") && fields.length > 0) {
    const labels = FIELD_LABELS_BY_ENTITY[event.entity_type] ?? SERVER_FIELD_LABELS;
    return `Campos alterados: ${fields.map((field) => labels[field] ?? field).join(", ")}`;
  }
  return null;
}

export function HistorySection({
  queryKey,
  queryFn,
  subtitle,
  ariaLabel,
}: {
  queryKey: QueryKey;
  queryFn: (signal: AbortSignal) => Promise<HistoryEvent[]>;
  subtitle: string;
  ariaLabel: string;
}) {
  const historyQuery = useQuery({ queryKey, queryFn: ({ signal }) => queryFn(signal) });

  return (
    <ItpSectionCard title="Histórico" subtitle={subtitle} collapsible>
      {historyQuery.isPending ? (
        <LoadingBlock title="Carregando histórico" />
      ) : historyQuery.error ? (
        <QueryErrorState error={toApiError(historyQuery.error)} onRetry={() => void historyQuery.refetch()} />
      ) : historyQuery.data.length === 0 ? (
        <p className="itp-muted">Nenhum evento registrado.</p>
      ) : (
        <ol className="itp-timeline" aria-label={ariaLabel}>
          {historyQuery.data.map((event) => {
            const detail = describeHistoryChange(event);
            return (
              <li key={event.id} className="itp-timeline-item">
                <p className="itp-timeline-meta">
                  <strong>{HISTORY_EVENT_LABELS[event.event_type] ?? event.event_type}</strong> · {event.actor_name} ·{" "}
                  <time dateTime={event.occurred_at}>{formatDateTime(event.occurred_at)}</time>
                </p>
                {detail ? <p className="itp-muted">{detail}</p> : null}
              </li>
            );
          })}
        </ol>
      )}
    </ItpSectionCard>
  );
}
