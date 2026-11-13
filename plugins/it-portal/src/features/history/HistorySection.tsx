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
  INTEGRATION_FIELD_LABELS,
  NETWORK_FIELD_LABELS,
  SERVER_FIELD_LABELS,
  WORKSTATION_FIELD_LABELS,
  SERVICE_FIELD_LABELS,
} from "../../content/labels";

type Ref = { code?: string; name?: string } | undefined;

const FIELD_LABELS_BY_ENTITY: Partial<Record<HistoryEntityType, Record<string, string>>> = {
  server: SERVER_FIELD_LABELS,
  workstation: WORKSTATION_FIELD_LABELS,
  action_plan: ACTION_FIELD_LABELS,
  service: SERVICE_FIELD_LABELS,
  database_instance: DATABASE_FIELD_LABELS,
  network: NETWORK_FIELD_LABELS,
  integration: INTEGRATION_FIELD_LABELS,
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
    return `${refLabel(changes.service as Ref)} usa ${refLabel(changes.database_instance as Ref)}`;
  }
  if (event.entity_type === "server_network_link") {
    const ip = typeof changes.ip_address === "string" ? ` com IP ${changes.ip_address}` : "";
    return `${refLabel(changes.server as Ref)} na rede ${refLabel(changes.network as Ref)}${ip}`;
  }
  if (event.entity_type === "service_dependency") {
    return `${refLabel(changes.dependent_service as Ref)} depende de ${refLabel(changes.required_service as Ref)}`;
  }
  if (event.entity_type === "host_service_action") {
    const service = typeof changes.service === "string" ? changes.service : "Serviço Windows";
    const action = changes.action === "restart" ? "Reiniciar" : changes.action === "stop" ? "Interromper" : "Iniciar";
    const statuses: Record<string, string> = {
      succeeded: "confirmado no Windows", failed: "falhou no Windows",
      timeout: "sem confirmação", queued: "aguardando",
    };
    const outcome = typeof changes.status === "string" ? statuses[changes.status] ?? changes.status : "solicitado";
    return `${service} · ${action} · ${outcome}`;
  }
  if (event.entity_type === "host_service_preference") {
    const label = typeof changes.service === "string" ? changes.service : "Serviço Windows";
    const favorite = changes.is_favorite as { to?: boolean } | undefined;
    const criticality = changes.criticality as { to?: string } | undefined;
    const rank: Record<string, string> = { normal: "Normal", high: "Alta", critical: "Crítica" };
    const favText = favorite?.to ? "Adicionado aos favoritos" : "Removido dos favoritos";
    return `${label} · ${favText} · Criticidade ${rank[criticality?.to ?? "normal"] ?? "Normal"}`;
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
