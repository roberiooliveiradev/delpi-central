import type { Integration } from "../../api/itPortalApi";
import { ResourceLink } from "../inventory/LinkSections";

type Side = "source" | "target";

export function endpointText(integration: Integration, side: Side): string {
  const service = side === "source" ? integration.source_service : integration.target_service;
  if (service) return `${service.code} · ${service.name}`;
  const external = side === "source" ? integration.source_external_name : integration.target_external_name;
  return `${external ?? "—"} (externo)`;
}

/** Ponta interna vira link para o serviço; ponta externa é apenas o nome declarado. */
export function IntegrationEndpoint({ integration, side }: { integration: Integration; side: Side }) {
  const service = side === "source" ? integration.source_service : integration.target_service;
  if (service) {
    return (
      <span className="itp-cell-stack">
        <ResourceLink label={service.name} target={{ serviceId: service.id }} title={`Abrir ${service.name}`} />
        <span className="itp-muted">{service.archived ? `${service.code} · arquivado` : service.code}</span>
      </span>
    );
  }
  const external = side === "source" ? integration.source_external_name : integration.target_external_name;
  return (
    <span className="itp-cell-stack">
      <span>{external ?? "—"}</span>
      <span className="itp-muted">Sistema externo</span>
    </span>
  );
}
