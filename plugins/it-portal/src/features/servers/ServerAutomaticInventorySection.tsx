import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Cpu,
  Database,
  HardDrive,
  Info,
  MemoryStick,
  Network,
  RefreshCw,
  ServerCog,
  type LucideIcon,
} from "lucide-react";
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

const SECTION_LABELS: Record<string, string> = {
  os: "Sistema",
  cpu: "CPU",
  memory: "Memória",
  swap: "Swap",
  volumes: "Discos",
  host_nics: "Rede",
  systemd_services: "Serviços",
  windows_services: "Serviços",
  docker: "Docker",
  docker_summary: "Docker",
};

type ReadonlyRecord = Record<string, unknown>;
type Level = "normal" | "caution" | "critical";

function objectValue(value: unknown): ReadonlyRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as ReadonlyRecord
    : {};
}

function arrayValue(value: unknown): ReadonlyRecord[] {
  return Array.isArray(value)
    ? value.filter((item) => item !== null && typeof item === "object" && !Array.isArray(item)) as ReadonlyRecord[]
    : [];
}

function textValue(value: unknown): string {
  return typeof value === "string" && value.trim() ? value : "—";
}

function numberValue(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function bytesLabel(value: unknown): string {
  const bytes = numberValue(value);
  if (bytes === null) return "—";
  if (bytes >= 1024 ** 3) return (bytes / (1024 ** 3)).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " GiB";
  return (bytes / (1024 ** 2)).toLocaleString("pt-BR", { maximumFractionDigits: 0 }) + " MiB";
}

function numberLabel(value: unknown): string {
  const number = numberValue(value);
  return number === null ? "—" : number.toLocaleString("pt-BR");
}

function percentValue(value: unknown): number | null {
  const number = numberValue(value);
  return number !== null && number <= 100 ? number : null;
}

function percentLabel(value: number | null): string {
  return value === null ? "—" : value.toLocaleString("pt-BR", { maximumFractionDigits: 2 }) + "%";
}

function stateLabel(value: unknown): string {
  const state = textValue(value);
  const labels: Record<string, string> = {
    running: "Em execução",
    active: "Ativo",
    started: "Iniciado",
    stopped: "Parado",
    inactive: "Inativo",
    failed: "Falha",
    automatic: "Automático",
    manual: "Manual",
    disabled: "Desativado",
    up: "Ativa",
    down: "Inativa",
    connected: "Conectada",
    disconnected: "Desconectada",
  };
  return labels[state.toLowerCase()] ?? state;
}

function uptimeLabel(value: unknown): string {
  const seconds = numberValue(value);
  if (seconds === null) return "—";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return days + "d " + hours + "h " + minutes + "min";
}

function usageLevel(value: number | null): Level {
  if (value !== null && value >= 90) return "critical";
  if (value !== null && value >= 75) return "caution";
  return "normal";
}

function Progress({
  value,
  label,
  level = "normal",
}: {
  value: number | null;
  label: string;
  level?: Level;
}) {
  return (
    <div
      className={"itp-observation-progress is-" + level}
      role={value === null ? undefined : "progressbar"}
      aria-label={label}
      aria-valuemin={value === null ? undefined : 0}
      aria-valuemax={value === null ? undefined : 100}
      aria-valuenow={value === null ? undefined : Number(value.toFixed(2))}
    >
      <span style={{ width: String(value ?? 0) + "%" }} />
    </div>
  );
}

function Metric({
  label,
  value,
  detail,
  icon: Icon,
  progress,
  level,
}: {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  progress?: number | null;
  level?: Level;
}) {
  return (
    <div className="itp-observation-metric">
      <div className="itp-observation-metric__top">
        <span className="itp-observation-metric__label">{label}</span>
        <Icon size={19} strokeWidth={1.7} aria-hidden="true" />
      </div>
      <strong className="itp-observation-metric__value">{value}</strong>
      <span className="itp-observation-metric__detail">{detail}</span>
      {progress !== undefined ? <Progress value={progress} label={"Utilização de " + label} level={level} /> : null}
    </div>
  );
}

function Surface({
  title,
  icon: Icon,
  children,
  className = "",
}: {
  title: string;
  icon: LucideIcon;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={"itp-observation-surface " + className}>
      <h3 className="itp-observation-surface__heading">
        <Icon size={18} strokeWidth={1.7} aria-hidden="true" />
        {title}
      </h3>
      {children}
    </section>
  );
}

function Detail({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="itp-observation-detail">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function DivergencesBlock({ items }: { items: ObservationDivergence[] }) {
  if (!items.length) return null;
  return (
    <Surface title="Diferenças em relação ao cadastro" icon={AlertTriangle} className="itp-observation-surface--warning">
      <p className="itp-muted">Os valores são apenas comparados. A coleta não altera o cadastro manual.</p>
      <div className="itp-observation-differences">
        {items.map((item) => (
          <div className="itp-observation-difference" key={item.field}>
            <strong>{FIELD_LABELS[item.field] ?? item.field}</strong>
            <dl className="itp-observation-difference__values">
              <Detail label="Cadastrado" value={orDash(item.registered)} />
              <Detail label="Observado" value={orDash(item.observed)} />
            </dl>
          </div>
        ))}
      </div>
    </Surface>
  );
}

function ObservationBody({ observation }: { observation: Observation }) {
  const summary = objectValue(observation.summary);
  const os = objectValue(summary.os);
  const memory = objectValue(summary.memory);
  const swap = objectValue(summary.swap);
  const volumes = arrayValue(summary.volumes);
  const nics = arrayValue(summary.host_nics);
  const isWindows = observation.source === "windows_host_collector";
  const services = arrayValue(isWindows ? summary.windows_services : summary.systemd_services);
  const docker = objectValue(summary.docker_summary);
  const total = numberValue(memory.total_bytes);
  const available = numberValue(memory.available_bytes);
  const memoryUsed = total !== null && total > 0 && available !== null && available <= total
    ? percentValue((100 * (total - available)) / total)
    : null;
  const cpuUsed = isWindows ? percentValue(summary.cpu_usage_percent) : null;
  const presentation = observation.presentation_status ?? "unavailable";
  const diskUsages = volumes.map((volume) => {
    const explicit = percentValue(volume.used_percent);
    const used = numberValue(volume.used_bytes);
    const size = numberValue(volume.size_bytes);
    return explicit !== null
      ? explicit
      : size !== null && size > 0 && used !== null ? percentValue((100 * used) / size) : null;
  });
  const maximumDisk = diskUsages.filter((value): value is number => value !== null);
  const highestDisk = maximumDisk.length ? Math.max(...maximumDisk) : null;
  const sectionsStatus = Object.entries(observation.sections_status ?? {});
  const osName = [os.name, os.version].filter((value): value is string => typeof value === "string" && !!value.trim()).join(" ");

  return (
    <div className="itp-observation">
      <div className="itp-observation-hero">
        <div className="itp-observation-hero__identity">
          <span className="itp-observation-hero__icon"><Activity size={23} strokeWidth={1.65} aria-hidden="true" /></span>
          <div>
            <p className="itp-server-workspace__eyebrow">Última leitura do host</p>
            <h3>{isWindows ? "Windows Server" : "Servidor Linux"}</h3>
            <p>Coletado em <time dateTime={observation.observed_at}>{formatDateTime(observation.observed_at)}</time></p>
          </div>
        </div>
        <div className="itp-observation-hero__badges">
          <span className={"itp-observation-status is-" + presentation}>
            {presentation === "available" ? <CheckCircle2 size={15} aria-hidden="true" /> : <Info size={15} aria-hidden="true" />}
            {PRESENTATION_LABELS[presentation]}
          </span>
          <span className="itp-observation-source">{isWindows ? "Coletor Windows" : "Coletor Linux"}</span>
        </div>
      </div>

      <div className="itp-observation-metrics">
        <Metric
          label="CPU"
          icon={Cpu}
          value={isWindows ? percentLabel(cpuUsed) : numberLabel(summary.cpu_logical)}
          detail={isWindows ? numberLabel(summary.cpu_logical) + " CPUs lógicas · amostra" : "CPUs lógicas · uso não coletado"}
          progress={isWindows ? cpuUsed : undefined}
          level={usageLevel(cpuUsed)}
        />
        <Metric
          label="Memória"
          icon={MemoryStick}
          value={percentLabel(memoryUsed)}
          detail={bytesLabel(memory.available_bytes) + " livres de " + bytesLabel(memory.total_bytes)}
          progress={memoryUsed}
          level={usageLevel(memoryUsed)}
        />
        {isWindows ? (
          <Metric
            label="Atividade"
            icon={Clock3}
            value={uptimeLabel(summary.uptime_seconds)}
            detail="Tempo desde a última inicialização"
          />
        ) : (
          <Metric
            label="Serviços"
            icon={Activity}
            value={numberLabel(services.length)}
            detail="Serviços verificados na coleta"
          />
        )}
        <Metric
          label="Armazenamento"
          icon={HardDrive}
          value={highestDisk === null ? "—" : percentLabel(highestDisk)}
          detail={volumes.length + (volumes.length === 1 ? " volume observado" : " volumes observados") + " · maior ocupação"}
          progress={highestDisk}
          level={usageLevel(highestDisk)}
        />
      </div>

      <div className="itp-observation-layout">
        <Surface title="Volumes e armazenamento" icon={HardDrive} className="itp-observation-surface--wide">
          {volumes.length ? (
            <div className="itp-observation-volumes">
              {volumes.map((volume, index) => {
                const usage = diskUsages[index];
                const level = usageLevel(usage);
                return (
                  <div className="itp-observation-volume" key={String(volume.mount_point ?? index)}>
                    <div className="itp-observation-volume__heading">
                      <span className="itp-observation-volume__disk"><HardDrive size={16} aria-hidden="true" /> {textValue(volume.mount_point)}</span>
                      <span className={"itp-observation-volume__percentage is-" + level}>{percentLabel(usage)}</span>
                    </div>
                    <Progress value={usage} label={"Ocupação do volume " + textValue(volume.mount_point)} level={level} />
                    <div className="itp-observation-volume__footer">
                      <span>{bytesLabel(volume.used_bytes)} utilizados de {bytesLabel(volume.size_bytes)}</span>
                      {level === "critical" ? <span className="itp-observation-volume__attention"><AlertTriangle size={13} aria-hidden="true" /> Uso elevado</span> : null}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : <p className="itp-muted">Nenhum volume informado na última coleta.</p>}
        </Surface>

        <Surface title="Sistema e hardware" icon={ServerCog}>
          <dl className="itp-observation-detail-grid">
            <Detail label="Sistema operacional" value={orDash(osName)} />
            <Detail label="Arquitetura" value={textValue(os.architecture)} />
            <Detail label="Kernel / build" value={textValue(os.kernel)} />
            <Detail label="Processadores lógicos" value={numberLabel(summary.cpu_logical)} />
            <Detail label="Memória total" value={bytesLabel(memory.total_bytes)} />
            {!isWindows ? <Detail label="Swap total" value={bytesLabel(swap.total_bytes)} /> : null}
          </dl>
        </Surface>

        <Surface title="Interfaces de rede" icon={Network}>
          {nics.length ? (
            <div className="itp-observation-compact-list">
              {nics.map((nic, index) => {
                const addresses = Array.isArray(nic.addresses)
                  ? nic.addresses.filter((address): address is string => typeof address === "string")
                  : [];
                return (
                  <div className="itp-observation-compact-row" key={String(nic.name ?? index)}>
                    <div>
                      <strong>{textValue(nic.name)}</strong>
                      <p>{addresses.length ? addresses.join(", ") : "Nenhum endereço informado"}</p>
                    </div>
                    {nic.state ? <span className="itp-observation-inline-status">{stateLabel(nic.state)}</span> : null}
                  </div>
                );
              })}
            </div>
          ) : <p className="itp-muted">Nenhuma interface observada.</p>}
        </Surface>

        <Surface title={isWindows ? "Serviços Windows observados" : "Serviços observados"} icon={Activity}>
          {services.length ? (
            <div className="itp-observation-compact-list">
              {services.map((service, index) => {
                const state = textValue(service.active_state);
                const running = ["running", "active", "started"].includes(state.toLowerCase());
                return (
                  <div className="itp-observation-compact-row" key={String(service.name ?? index)}>
                    <div>
                      <strong>{textValue(service.name)}</strong>
                      {service.sub_state ? <p>{isWindows ? "Inicialização: " : "Subestado: "}{stateLabel(service.sub_state)}</p> : null}
                    </div>
                    <span className={"itp-observation-inline-status" + (running ? " is-running" : "")}>
                      {running ? <CheckCircle2 size={13} aria-hidden="true" /> : null}
                      {stateLabel(state)}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : <p className="itp-muted">Nenhum serviço informado nesta coleta.</p>}
        </Surface>

        {!isWindows ? (
          <Surface title="Docker" icon={Database}>
            {docker.available ? (
              <dl className="itp-observation-detail-grid">
                <Detail label="Versão" value={textValue(docker.server_version)} />
                <Detail label="Containers" value={numberLabel(docker.containers_total)} />
                <Detail label="Em execução" value={numberLabel(docker.containers_running)} />
                <Detail label="Imagens" value={numberLabel(docker.images)} />
              </dl>
            ) : (
              <p className="itp-muted">Docker indisponível nesta coleta{docker.unavailable_reason ? " (" + (docker.unavailable_reason === "no_permission" ? "sem permissão para consultar" : String(docker.unavailable_reason)) + ")" : ""}.</p>
            )}
          </Surface>
        ) : null}
      </div>

      <DivergencesBlock items={observation.divergences ?? []} />

      <details className="itp-observation-technical">
        <summary>Informações técnicas e diagnóstico da coleta</summary>
        <dl className="itp-observation-detail-grid">
          <Detail label="Origem" value={observation.source} />
          <Detail label="Status da coleta" value={observation.status} />
          <Detail label="Recebido em" value={formatDateTime(observation.received_at)} />
          <Detail label="Versão do esquema" value={observation.schema_version} />
          <Detail label="Identificador da execução" value={<code className="itp-code">{observation.run_id}</code>} />
        </dl>
        {sectionsStatus.length ? (
          <div className="itp-observation-section-states" aria-label="Estado das áreas coletadas">
            {sectionsStatus.map(([key, status]) => (
              <span key={key} className="itp-observation-section-state">
                {SECTION_LABELS[key] ?? key}: {String(status)}
              </span>
            ))}
          </div>
        ) : null}
      </details>
    </div>
  );
}

export function ServerAutomaticInventorySection({ serverId }: { serverId: string }) {
  const { capabilities } = usePortal();
  const canView = capabilities?.can_view_servers === true;

  const query = useQuery({
    queryKey: queryKeys.serverObservationLatest(serverId),
    queryFn: ({ signal }) => itPortalApi.getLatestObservation(serverId, signal),
    enabled: canView,
    refetchInterval: canView ? 60_000 : false,
  });

  if (!canView) return null;

  return (
    <div className="itp-observation-section">
      <div className="itp-observation-toolbar">
        <p>Dados observados no servidor, sem modificar o cadastro manual. Atualização da visualização a cada minuto.</p>
        <button
          type="button"
          className="itp-observation-refresh"
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
          aria-label="Atualizar inventário automático"
        >
          <RefreshCw size={16} aria-hidden="true" />
          {query.isFetching ? "Atualizando…" : "Atualizar agora"}
        </button>
      </div>
      {query.isPending ? <LoadingBlock title="Carregando inventário automático" /> : null}
      {query.error ? <QueryErrorState error={toApiError(query.error)} onRetry={() => void query.refetch()} /> : null}
      {!query.isPending && !query.error && query.data == null ? (
        <ItpSectionCard title="Inventário automático">
          <ItpStateBanner>
            <p className="itp-state-text">Nenhuma observação automática registrada para este servidor ainda.</p>
          </ItpStateBanner>
        </ItpSectionCard>
      ) : null}
      {query.data ? <ObservationBody observation={query.data} /> : null}
    </div>
  );
}
