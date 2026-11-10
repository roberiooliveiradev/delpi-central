import { useQuery } from "@tanstack/react-query";

import { itPortalApi, type ActionStatus, type HistoryEvent } from "../../api/itPortalApi";
import { formatDateTime } from "../../app/format";
import { ItpSectionCard } from "../../app/itPortalUi";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import {
  ACTION_FIELD_LABELS,
  ACTION_STATUS_LABELS,
  HISTORY_EVENT_LABELS,
  SERVER_FIELD_LABELS,
} from "../../content/labels";

function describeChange(event: HistoryEvent): string | null {
  const changes = event.changes ?? {};
  if (event.event_type === "action_plan_status_changed") {
    const status = changes.status as { from?: string; to?: string } | undefined;
    const label = (value?: string) => ACTION_STATUS_LABELS[value as ActionStatus] ?? value ?? "—";
    return status ? `De ${label(status.from)} para ${label(status.to)}` : null;
  }
  const fields = Object.keys(changes);
  if (event.event_type.endsWith("_updated") && fields.length > 0) {
    const labels = event.entity_type === "action_plan" ? ACTION_FIELD_LABELS : SERVER_FIELD_LABELS;
    return `Campos alterados: ${fields.map((field) => labels[field] ?? field).join(", ")}`;
  }
  return null;
}

export function ServerHistorySection({ serverId }: { serverId: string }) {
  const historyQuery = useQuery({
    queryKey: queryKeys.history(serverId),
    queryFn: ({ signal }) => itPortalApi.listHistory(serverId, signal),
  });

  return (
    <ItpSectionCard title="Histórico" subtitle="Últimos 50 eventos auditados deste servidor." collapsible>
      {historyQuery.isPending ? (
        <LoadingBlock title="Carregando histórico" />
      ) : historyQuery.error ? (
        <QueryErrorState error={toApiError(historyQuery.error)} onRetry={() => void historyQuery.refetch()} />
      ) : historyQuery.data.length === 0 ? (
        <p className="itp-muted">Nenhum evento registrado.</p>
      ) : (
        <ol className="itp-timeline" aria-label="Histórico do servidor">
          {historyQuery.data.map((event) => {
            const detail = describeChange(event);
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
