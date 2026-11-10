import { useQuery } from "@tanstack/react-query";
import { AlarmClock, ListTodo, Plus, Server as ServerIcon, ShieldAlert } from "lucide-react";
import { useState } from "react";

import { itPortalApi, type Dashboard } from "../../api/itPortalApi";
import { ActionStatusBadge, CriticalityBadge, EnvironmentBadge, PriorityBadge } from "../../app/badges";
import { formatCount, formatDate, formatDateTime } from "../../app/format";
import {
  ItpActionButton,
  ItpEmptyState,
  ItpKpiCard,
  ItpPageHero,
  ItpSectionCard,
  ItpStatusBadge,
} from "../../app/itPortalUi";
import { navigateTo, spaNavigate } from "../../app/navigation";
import { toApiError, usePortal } from "../../app/PortalContext";
import { ForbiddenState, LoadingBlock, QueryErrorState } from "../../app/QueryStates";
import { queryKeys } from "../../app/queryKeys";
import { buildPath } from "../../app/routes";
import { ServerFormModal } from "../servers/ServerFormModal";

const UPCOMING_AREAS = ["Monitoramento", "Descoberta automática", "Integração com GLPI", "Notificações"];

export function HomePage() {
  const { basePath, capabilities } = usePortal();
  const [creating, setCreating] = useState(false);
  const canView = capabilities?.can_view_servers === true;
  const canManage = capabilities?.can_manage_servers === true;

  const dashboardQuery = useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: ({ signal }) => itPortalApi.dashboard(signal),
    enabled: canView,
  });

  const createButton = canManage ? (
    <ItpActionButton variant="primary" onClick={() => setCreating(true)}>
      <Plus size={16} strokeWidth={1.75} aria-hidden="true" /> Cadastrar servidor
    </ItpActionButton>
  ) : null;

  let body;
  if (!canView) {
    body = <ForbiddenState message="Você tem acesso ao Portal de TI, mas não à visualização do inventário de servidores." />;
  } else if (dashboardQuery.isPending) {
    body = <LoadingBlock title="Carregando visão geral" />;
  } else if (dashboardQuery.error || !dashboardQuery.data) {
    body = <QueryErrorState error={toApiError(dashboardQuery.error)} onRetry={() => void dashboardQuery.refetch()} />;
  } else if (dashboardQuery.data.servers.total === 0) {
    body = (
      <ItpEmptyState
        title="Nenhum servidor cadastrado"
        message={
          canManage
            ? "Comece cadastrando o primeiro servidor da infraestrutura. Os indicadores desta página são calculados a partir do inventário."
            : "O inventário ainda está vazio. Peça a um responsável com permissão de gestão para cadastrar os servidores."
        }
      >
        {createButton}
      </ItpEmptyState>
    );
  } else {
    body = <DashboardContent data={dashboardQuery.data} basePath={basePath} />;
  }

  return (
    <>
      <ItpPageHero
        aria-label="Portal de TI"
        eyebrow="Portal de TI"
        title={capabilities?.display_name ? `Olá, ${capabilities.display_name.split(" ")[0]}` : "Portal de TI"}
        description="Inventário de servidores e planos de ação da infraestrutura DELPI."
        actions={dashboardQuery.data && dashboardQuery.data.servers.total > 0 ? createButton : null}
      />
      {body}
      <ItpSectionCard title="Próximas áreas" subtitle="Ainda não disponíveis nesta etapa do Portal de TI.">
        <ul className="itp-chip-list" aria-label="Áreas indisponíveis">
          {UPCOMING_AREAS.map((area) => (
            <li key={area}>
              <ItpStatusBadge label={`${area} · indisponível`} variant="neutral" />
            </li>
          ))}
        </ul>
      </ItpSectionCard>
      {creating ? (
        <ServerFormModal
          open
          onClose={() => setCreating(false)}
          onSaved={(server) => navigateTo(buildPath(basePath, { serverId: server.id }))}
        />
      ) : null}
    </>
  );
}

function DashboardContent({ data, basePath }: { data: Dashboard; basePath: string }) {
  const serversHref = buildPath(basePath, "servers");
  const actionsHref = buildPath(basePath, "action_plans");

  return (
    <>
      <div className="itp-kpi-grid" role="group" aria-label="Indicadores">
        <ItpKpiCard
          label="Servidores ativos"
          value={formatCount(data.servers.total)}
          hint="Cadastros não arquivados"
          icon={<ServerIcon size={18} strokeWidth={1.75} aria-hidden="true" />}
        />
        <ItpKpiCard
          label="Criticidade alta ou crítica"
          value={formatCount(data.servers.high_or_critical)}
          hint="Servidores ativos"
          tone={data.servers.high_or_critical > 0 ? "warning" : "default"}
          icon={<ShieldAlert size={18} strokeWidth={1.75} aria-hidden="true" />}
        />
        {data.action_plans ? (
          <>
            <ItpKpiCard
              label="Ações abertas"
              value={formatCount(data.action_plans.open)}
              hint="Pendentes ou em andamento"
              icon={<ListTodo size={18} strokeWidth={1.75} aria-hidden="true" />}
            />
            <ItpKpiCard
              label="Ações atrasadas"
              value={formatCount(data.action_plans.overdue)}
              hint={`Prazo anterior a ${formatDate(data.reference_date)}`}
              tone={data.action_plans.overdue > 0 ? "negative" : "positive"}
              icon={<AlarmClock size={18} strokeWidth={1.75} aria-hidden="true" />}
            />
          </>
        ) : null}
      </div>

      <div className="itp-detail-grid">
        <ItpSectionCard
          title="Servidores recentes"
          subtitle="Últimos servidores cadastrados."
          actions={
            <ItpActionButton variant="link" href={serversHref} title="Ver inventário" onClick={spaNavigate(serversHref)}>
              Ver todos
            </ItpActionButton>
          }
        >
          <ul className="itp-link-list">
            {data.recent_servers.map((server) => {
              const href = buildPath(basePath, { serverId: server.id });
              return (
                <li key={server.id} className="itp-link-list-item">
                  <a href={href} onClick={spaNavigate(href)} className="itp-link-list-anchor">
                    <span className="itp-cell-stack">
                      <strong>{server.name}</strong>
                      <span className="itp-muted">
                        {server.hostname} · cadastrado {formatDateTime(server.created_at)}
                      </span>
                    </span>
                  </a>
                  <span className="itp-badge-group">
                    <EnvironmentBadge value={server.environment} />
                    <CriticalityBadge value={server.criticality} />
                  </span>
                </li>
              );
            })}
          </ul>
        </ItpSectionCard>

        {data.attention_action_plans ? (
          <ItpSectionCard
            title="Ações que pedem atenção"
            subtitle="Abertas, ordenadas por atraso, prazo e prioridade."
            actions={
              <ItpActionButton variant="link" href={actionsHref} title="Ver planos de ação" onClick={spaNavigate(actionsHref)}>
                Ver todos
              </ItpActionButton>
            }
          >
            {data.attention_action_plans.length === 0 ? (
              <p className="itp-muted">Nenhuma ação aberta no momento.</p>
            ) : (
              <ul className="itp-link-list">
                {data.attention_action_plans.map((plan) => {
                  const href = buildPath(basePath, { serverId: plan.server_id });
                  return (
                    <li key={plan.id} className="itp-link-list-item">
                      <a href={href} onClick={spaNavigate(href)} className="itp-link-list-anchor">
                        <span className="itp-cell-stack">
                          <strong>{plan.title}</strong>
                          <span className="itp-muted">
                            {plan.server.name} · prazo {formatDate(plan.due_date)}
                          </span>
                        </span>
                      </a>
                      <span className="itp-badge-group">
                        <PriorityBadge value={plan.priority} />
                        <ActionStatusBadge value={plan.status} overdue={plan.is_overdue} />
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
          </ItpSectionCard>
        ) : null}
      </div>
    </>
  );
}
