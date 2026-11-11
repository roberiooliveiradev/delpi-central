import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";

import {
  itPortalApi,
  type Observation,
  type ObservationDivergence,
  type ObservationPresentationStatus,
} from "../../api/itPortalApi";
import { formatDateTime, orDash } from "../../app/format";
import { ItpSectionCard, ItpStateBanner } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";

const PRESENTATION_LABELS: Record<ObservationPresentationStatus, string> = {
  available: "Disponível",
  partial: "Parcial",
  stale: "Desatualizada",
  unavailable: "Indisponível",
};

const FIELD_LABELS: Record<string, string> = {
  hostname: "Hostname",
  operating_system: "Sistema operacional",
  ip_address: "Endereço IP",
};

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="itp-field">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function bytesLabel(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const gb = value / (1024 ** 3);
  if (gb >= 1) return `${gb.toFixed(1)} GiB`;
  const mb = value / (1024 ** 2);
  return `${mb.toFixed(0)} MiB`;
}

function numberLabel(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return String(value);
}

function DivergencesBlock({ items }: { items: ObservationDivergence[] }) {
  if (!items.length) return null;
  return (
    <div className="itp-observation-divergences">
      <h3 className="itp-subsection-title">Divergências em relação ao cadastro</h3>
      <p className="itp-muted">
        Somente leitura nesta etapa — o inventário automático não altera o cadastro manual.
      </p>
      <ul className="itp-plain-list">
        {items.map((item) => (
          <li key={item.field}>
            <strong>{FIELD_LABELS[item.field] ?? item.field}</strong>: cadastro «{orDash(item.registered)}»
            {" · "}
            observado «{orDash(item.observed)}»
          </li>
        ))}
      </ul>
    </div>
  );
}

function ObservationBody({ observation }: { observation: Observation }) {
  const summary = observation.summary ?? {};
  const os = (summary.os as Record<string, unknown> | undefined) ?? {};
  const memory = (summary.memory as Record<string, unknown> | undefined) ?? {};
  const swap = (summary.swap as Record<string, unknown> | undefined) ?? {};
  const volumes = (summary.volumes as Array<Record<string, unknown>> | undefined) ?? [];
  const nics = (summary.host_nics as Array<Record<string, unknown>> | undefined) ?? [];
  const services = (summary.systemd_services as Array<Record<string, unknown>> | undefined) ?? [];
  const docker = (summary.docker_summary as Record<string, unknown> | undefined) ?? {};
  const presentation = (observation.presentation_status ?? "unavailable") as ObservationPresentationStatus;

  return (
    <>
      <dl className="itp-field-list">
        <Field label="Coletado em" value={formatDateTime(observation.observed_at)} />
        <Field label="Origem" value={observation.source} />
        <Field label="Status da coleta" value={observation.status} />
        <Field label="Situação exibida" value={PRESENTATION_LABELS[presentation] ?? presentation} />
      </dl>

      <DivergencesBlock items={observation.divergences ?? []} />

      <div className="itp-detail-grid">
        <ItpSectionCard title="SO e hardware">
          <dl className="itp-field-list">
            <Field
              label="Sistema"
              value={orDash([os.name, os.version].filter(Boolean).join(" ") || null)}
            />
            <Field label="Kernel" value={orDash(typeof os.kernel === "string" ? os.kernel : null)} />
            <Field
              label="Arquitetura"
              value={orDash(typeof os.architecture === "string" ? os.architecture : null)}
            />
            <Field label="CPUs lógicas" value={numberLabel(summary.cpu_logical as number | undefined)} />
          </dl>
        </ItpSectionCard>
        <ItpSectionCard title="Memória e disco">
          <dl className="itp-field-list">
            <Field label="Memória total" value={bytesLabel(memory.total_bytes as number | undefined)} />
            <Field label="Memória disponível" value={bytesLabel(memory.available_bytes as number | undefined)} />
            <Field label="Swap total" value={bytesLabel(swap.total_bytes as number | undefined)} />
          </dl>
          {volumes.length ? (
            <ul className="itp-plain-list">
              {volumes.slice(0, 8).map((volume) => (
                <li key={String(volume.mount_point)}>
                  {String(volume.mount_point)} — {bytesLabel(volume.used_bytes as number | undefined)} /{" "}
                  {bytesLabel(volume.size_bytes as number | undefined)}
                  {volume.used_percent != null ? ` (${volume.used_percent}%)` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="itp-muted">Sem volumes nesta observação.</p>
          )}
        </ItpSectionCard>
        <ItpSectionCard title="Interfaces de host">
          {nics.length ? (
            <ul className="itp-plain-list">
              {nics.map((nic) => (
                <li key={String(nic.name)}>
                  <strong>{String(nic.name)}</strong>
                  {nic.state ? ` (${String(nic.state)})` : ""}:{" "}
                  {Array.isArray(nic.addresses) && nic.addresses.length
                    ? nic.addresses.join(", ")
                    : "sem endereço"}
                </li>
              ))}
            </ul>
          ) : (
            <p className="itp-muted">Nenhuma interface de host na observação.</p>
          )}
        </ItpSectionCard>
        <ItpSectionCard title="Serviços observados">
          {services.length ? (
            <ul className="itp-plain-list">
              {services.map((service) => (
                <li key={String(service.name)}>
                  {String(service.name)} — {orDash(service.active_state as string | undefined)}
                  {service.sub_state ? ` / ${String(service.sub_state)}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="itp-muted">Nenhum serviço da allowlist nesta observação.</p>
          )}
        </ItpSectionCard>
        <ItpSectionCard title="Docker">
          {docker.available ? (
            <dl className="itp-field-list">
              <Field
                label="Versão"
                value={orDash(typeof docker.server_version === "string" ? docker.server_version : null)}
              />
              <Field label="Containers" value={numberLabel(docker.containers_total as number | undefined)} />
              <Field
                label="Em execução"
                value={numberLabel(docker.containers_running as number | undefined)}
              />
              <Field label="Imagens" value={numberLabel(docker.images as number | undefined)} />
            </dl>
          ) : (
            <p className="itp-muted">
              Docker indisponível nesta coleta
              {docker.unavailable_reason ? ` (${String(docker.unavailable_reason)})` : ""}.
            </p>
          )}
        </ItpSectionCard>
      </div>
    </>
  );
}

export function ServerAutomaticInventorySection({ serverId }: { serverId: string }) {
  const { capabilities } = usePortal();
  const canView = capabilities?.can_view_servers === true;

  const query = useQuery({
    queryKey: queryKeys.serverObservationLatest(serverId),
    queryFn: ({ signal }) => itPortalApi.getLatestObservation(serverId, signal),
    enabled: canView,
  });

  if (!canView) return null;

  return (
    <ItpSectionCard title="Inventário automático">
      <p className="itp-muted">
        Snapshot técnico coletado no host (somente leitura). Não substitui o cadastro manual.
      </p>
      {query.isPending ? <LoadingBlock title="Carregando inventário automático" /> : null}
      {query.error ? (
        <QueryErrorState error={toApiError(query.error)} onRetry={() => void query.refetch()} />
      ) : null}
      {!query.isPending && !query.error && query.data == null ? (
        <ItpStateBanner>
          <p className="itp-state-text">
            Nenhuma observação automática registrada para este servidor ainda.
          </p>
        </ItpStateBanner>
      ) : null}
      {query.data ? <ObservationBody observation={query.data} /> : null}
    </ItpSectionCard>
  );
}
