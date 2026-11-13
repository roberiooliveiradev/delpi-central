import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, CheckCircle2, Clock3, RefreshCw, Server as ServerIcon, ShieldCheck } from "lucide-react";

import { itPortalApi, type WindowsServicesHealth, type WindowsServiceIssue } from "../../api/itPortalApi";
import { formatCount, formatDateTime } from "../../app/format";
import { ItpSectionCard, ItpSemicircleGauge } from "../../app/itPortalUi";
import { navigateTo, spaNavigate } from "../../app/navigation";
import { toApiError } from "../../app/PortalContext";
import { LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";

import "./windowsServicesHealth.css";

function statusText(issue: WindowsServiceIssue): string {
  return issue.reason;
}

function toneFor(data: WindowsServicesHealth): "success" | "warning" | "danger" | "neutral" {
  if (data.unverified === data.total) return "neutral";
  if (data.health_percent === 100) return "success";
  if (data.stopped > 0) return "danger";
  return "warning";
}

export function WindowsServicesHealthPanel({ basePath }: { basePath: string }) {
  const health = useQuery({
    queryKey: queryKeys.windowsServicesHealth,
    queryFn: ({ signal }) => itPortalApi.windowsServicesHealth(signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
    refetchOnWindowFocus: true,
  });
  const data = health.data;

  return (
    <ItpSectionCard
      title="Saúde dos serviços Windows"
      subtitle="Serviços favoritos classificados como Alta ou Crítica, em todos os servidores cadastrados."
      actions={
        <button className="itp-wh__refresh" type="button" disabled={health.isFetching}
          onClick={() => void health.refetch()}
          title="Consulta a última coleta armazenada; não executa ações nos servidores.">
          <RefreshCw size={16} className={health.isFetching ? "is-spinning" : ""} aria-hidden="true" />
          Atualizar
        </button>
      }
    >
      {health.isPending ? <LoadingBlock title="Consultando os serviços monitorados" /> : null}
      {health.isError ? (
        <QueryErrorState error={toApiError(health.error)} onRetry={() => void health.refetch()} />
      ) : null}
      {data && !health.isError ? (
        <section className="itp-wh" aria-label="Monitor de saúde dos serviços Windows">
          {data.total === 0 ? (
            <div className="itp-wh__empty" role="status">
              <ShieldCheck size={30} aria-hidden="true" />
              <div>
                <strong>Nenhum serviço prioritário configurado</strong>
                <p>Em Servidores, marque os serviços Windows como favoritos e defina criticidade Alta ou Crítica. Eles aparecerão aqui automaticamente.</p>
              </div>
              <button type="button" onClick={() => navigateTo(buildPath(basePath, "servers"))}>
                Ver servidores
              </button>
            </div>
          ) : (
            <>
              <div className="itp-wh__overview">
                <div className="itp-wh__gauge">
                  <span className="itp-wh__eyebrow"><Activity size={15} aria-hidden="true" /> SAÚDE VERIFICADA</span>
                  <ItpSemicircleGauge
                    value={data.health_percent}
                    tone={toneFor(data)}
                    centerLabel="em execução"
                    size={220}
                    aria-label={"Saúde dos serviços Windows: " + data.health_percent + "% dos serviços prioritários verificados em execução"}
                  />
                  <strong className="itp-wh__message">
                    {data.health_percent === 100
                      ? "Todos os serviços prioritários estão ativos"
                      : data.unverified === data.total
                        ? "Sem confirmação recente dos serviços"
                        : "Há serviços que precisam de atenção"}
                  </strong>
                  <span className="itp-wh__timestamp">
                    <Clock3 size={13} aria-hidden="true" />
                    Painel atualizado em {formatDateTime(data.generated_at)}
                  </span>
                </div>
                <div className="itp-wh__metrics" role="group" aria-label="Contagem de serviços Windows prioritários">
                  <div className="itp-wh__metric is-total">
                    <span>Monitorados</span>
                    <strong>{formatCount(data.total)}</strong>
                    <small>Alta e Crítica</small>
                  </div>
                  <div className="itp-wh__metric is-running">
                    <span>Em execução</span>
                    <strong>{formatCount(data.running)}</strong>
                    <small>Confirmados na coleta</small>
                  </div>
                  <div className="itp-wh__metric is-stopped">
                    <span>Parados</span>
                    <strong>{formatCount(data.stopped)}</strong>
                    <small>Estado confirmado</small>
                  </div>
                  <div className="itp-wh__metric is-unverified">
                    <span>Outros / sem dados</span>
                    <strong>{formatCount(data.attention + data.unverified)}</strong>
                    <small>{data.attention} em atenção · {data.unverified} sem confirmação</small>
                  </div>
                </div>
              </div>
              <div className="itp-wh__servers">
                <div className="itp-wh__section-heading">
                  <h3>Saúde por servidor</h3>
                  <span>{data.servers.length} servidor(es) monitorado(s)</span>
                </div>
                <div className="itp-wh__server-grid">
                  {data.servers.map((server) => {
                    const href = buildPath(basePath, { serverId: server.server_id });
                    const percentage = server.health_percent ?? 0;
                    const state = percentage === 100 ? "healthy" : server.unverified === server.total ? "unknown" : "issue";
                    return (
                      <a key={server.server_id} href={href} onClick={spaNavigate(href)}
                        className={"itp-wh__server is-" + state}
                        aria-label={server.server_name + ": " + percentage + "% dos serviços em execução. Abrir servidor"}>
                        <span className="itp-wh__server-head">
                          <span className="itp-wh__server-icon"><ServerIcon size={17} aria-hidden="true" /></span>
                          <span className="itp-wh__server-identity">
                            <strong>{server.server_name}</strong>
                            <small>{server.hostname}</small>
                          </span>
                          <strong className="itp-wh__server-percentage">{percentage}%</strong>
                        </span>
                        <span className="itp-wh__progress-track" aria-hidden="true">
                          <span style={{ width: percentage + "%" }} />
                        </span>
                        <span className="itp-wh__server-meta">
                          <span>{server.running} de {server.total} em execução</span>
                          <span>{server.unverified > 0 ? "Sem confirmação" : "Coleta: " + formatDateTime(server.last_collected_at)}</span>
                        </span>
                      </a>
                    );
                  })}
                </div>
              </div>
              {data.issues_total > 0 ? (
                <div className="itp-wh__alerts">
                  <div className="itp-wh__section-heading">
                    <h3><AlertTriangle size={17} aria-hidden="true" /> Serviços que exigem atenção</h3>
                    <span>Exibindo {data.issues.length} de {data.issues_total}</span>
                  </div>
                  <ul className="itp-wh__alert-list">
                    {data.issues.map((issue) => {
                      const href = buildPath(basePath, { serverId: issue.server_id });
                      return (
                        <li key={issue.server_id + ":" + issue.service_key}>
                          <a href={href} onClick={spaNavigate(href)}>
                            <span className={"itp-wh__alert-dot is-" + issue.status} aria-hidden="true" />
                            <span className="itp-wh__alert-copy">
                              <strong>{issue.service_name}</strong>
                              <small>{issue.server_name} · {statusText(issue)}</small>
                            </span>
                            <span className={"itp-wh__priority is-" + issue.criticality}>
                              {issue.criticality === "critical" ? "Crítica" : "Alta"}
                            </span>
                          </a>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ) : (
                <p className="itp-wh__all-good">
                  <CheckCircle2 size={18} aria-hidden="true" />
                  Todos os serviços prioritários foram confirmados em execução na última coleta.
                </p>
              )}
              <p className="itp-wh__disclaimer">
                Leitura do inventário SCM a cada 5 minutos. O painel consulta a API a cada minuto.
                Coletas com mais de {data.stale_after_minutes} minutos são tratadas como sem confirmação, nunca como saudáveis.
              </p>
            </>
          )}
        </section>
      ) : null}
    </ItpSectionCard>
  );
}
