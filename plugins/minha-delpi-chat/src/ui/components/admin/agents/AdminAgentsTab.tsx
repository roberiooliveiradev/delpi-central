import { BarChart3, ExternalLink } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getChatAgentStats } from "../../../../data/api/chatApi";
import { buildChatAgentConfigHref, buildChatAgentHref } from "../../../../navigation/chatRoutes";
import { navigateChatHref } from "../../../../navigation/chatNavigation";
import { buildAdminAgentHref } from "../../../../navigation/adminNavigation";
import type { ChatAgentStats } from "../../../../data/api/chatTypes";
import { listAdminSpecializedAgents } from "../../../../data/api/adminApi";
import type { AdminSpecializedAgent } from "../../../../data/api/adminTypes";

import { AdminTabHeader } from "../shared/AdminTabHeader";
import { AgentMiniDashboard } from "./AgentMiniDashboard";
import { AgentSpecializationEditor } from "./AgentSpecializationEditor";
import { AgentsSummaryStrip } from "./AgentsSummaryStrip";
import {
  computeAgentsSummary,
  filterAgentsByCatalog,
  type AgentCatalogFilter,
} from "./agentsSummary";
import { agentPrimaryLabel, agentStatusBadge } from "./agentDisplay";
import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import "./AdminAgentsTab.css";

type AdminAgentsTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  initialAgentId?: string | null;
};

/**
 * Catálogo admin de especialização — a edição canônica também vive no Studio
 * (`ChatAgentBuilderPage` + `AgentSpecializationEditor`).
 */
export function AdminAgentsTab({ getAccessToken, initialAgentId }: AdminAgentsTabProps) {
  const [agents, setAgents] = useState<AdminSpecializedAgent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentStats, setAgentStats] = useState<ChatAgentStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [catalogFilter, setCatalogFilter] = useState<AgentCatalogFilter>("all");

  const summary = useMemo(() => computeAgentsSummary(agents), [agents]);
  const visibleAgents = useMemo(
    () => filterAgentsByCatalog(agents, catalogFilter),
    [agents, catalogFilter],
  );

  const selectedAgent = agents.find((agent) => agent.id === selectedAgentId) ?? null;

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const agentsResponse = await listAdminSpecializedAgents({ getAccessToken });
      const items = agentsResponse.items;
      setAgents(items);

      const preferred =
        (initialAgentId && items.some((agent) => agent.id === initialAgentId)
          ? initialAgentId
          : null) ??
        selectedAgentId ??
        items[0]?.id ??
        null;

      if (preferred && preferred !== selectedAgentId) {
        setSelectedAgentId(preferred);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar agentes.");
    } finally {
      setIsLoading(false);
    }
    // selectedAgentId omitido de propósito — só hidrata na carga / refresh
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getAccessToken, initialAgentId]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    if (!selectedAgentId) {
      setAgentStats(null);
      return;
    }

    navigateChatHref(buildAdminAgentHref(selectedAgentId));

    let cancelled = false;

    async function loadStats() {
      setIsLoadingStats(true);

      try {
        const stats = await getChatAgentStats(selectedAgentId!, {
          hours: 7,
          getAccessToken,
        });

        if (!cancelled) {
          setAgentStats(stats);
        }
      } catch {
        if (!cancelled) {
          setAgentStats(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingStats(false);
        }
      }
    }

    void loadStats();

    return () => {
      cancelled = true;
    };
  }, [selectedAgentId, getAccessToken]);

  function openAgentBuilder() {
    if (!selectedAgentId) {
      navigateChatHref(buildChatAgentHref(null));
      return;
    }

    navigateChatHref(buildChatAgentConfigHref(selectedAgentId));
  }

  return (
    <section className="mdc-admin-agents">
      <AdminTabHeader
        className="mdc-admin-agents__toolbar"
        eyebrow="Agentes"
        title="Especialização (catálogo)"
        description="Descoberta e atalho RAG/tools. A edição principal (identidade, prompt, skills e actions) é no Studio — use Abrir Studio (lista ou agente selecionado)."
        helpHint={ADMIN_HELP.pages.specialization}
        summary={
          <AgentsSummaryStrip
            summary={summary}
            activeFilter={catalogFilter}
            isLoading={isLoading}
            onFilterChange={setCatalogFilter}
          />
        }
        actions={
          <div className="mdc-admin-agents__toolbar-actions">
            <button
              type="button"
              className="mdc-admin-btn"
              disabled={isLoading}
              onClick={() => void loadData()}
            >
              {isLoading ? "Carregando..." : "Atualizar"}
            </button>
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              onClick={openAgentBuilder}
            >
              <ExternalLink size={15} aria-hidden="true" />
              <span>{selectedAgentId ? "Abrir Studio" : "Abrir lista no Studio"}</span>
            </button>
          </div>
        }
      />

      {error ? <p className="mdc-admin-agents__error">{error}</p> : null}

      <div className="mdc-admin-agents__layout mdc-admin-split">
        <aside className="mdc-admin-split__aside mdc-admin-agents__list">
          {isLoading ? (
            <p className="mdc-chat-muted">Carregando agentes…</p>
          ) : visibleAgents.length === 0 ? (
            <p className="mdc-chat-muted">
              {agents.length === 0
                ? "Nenhum agente oficial disponível."
                : "Nenhum agente neste filtro."}
            </p>
          ) : (
            <ul>
              {visibleAgents.map((agent) => {
                const badge = agentStatusBadge(agent);

                return (
                  <li key={agent.id}>
                    <button
                      type="button"
                      className={selectedAgentId === agent.id ? "is-selected" : undefined}
                      onClick={() => setSelectedAgentId(agent.id)}
                    >
                      <span className="mdc-admin-agents__list-head">
                        <strong>{agentPrimaryLabel(agent)}</strong>
                        <span
                          className={`mdc-admin-agents__badge mdc-admin-agents__badge--${badge.tone}`}
                        >
                          {badge.label}
                        </span>
                      </span>
                      <code className="mdc-admin-agents__agent-id">{agent.id}</code>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>

        <article className="mdc-admin-split__main mdc-admin-agents__editor">
          {!selectedAgent ? (
            <p className="mdc-chat-muted">Selecione um agente para configurar a especialização.</p>
          ) : (
            <>
              <div className="mdc-admin-agents__agent-title">
                <div className="mdc-admin-agents__agent-title-main">
                  <strong>{agentPrimaryLabel(selectedAgent)}</strong>
                  {(() => {
                    const badge = agentStatusBadge(selectedAgent);
                    return (
                      <span
                        className={`mdc-admin-agents__badge mdc-admin-agents__badge--${badge.tone}`}
                      >
                        {badge.label}
                      </span>
                    );
                  })()}
                </div>
                <code className="mdc-admin-agents__agent-id">{selectedAgent.id}</code>
              </div>

              <div className="mdc-admin-agents__stats">
                <div className="mdc-admin-agents__stats-title">
                  <BarChart3 size={16} aria-hidden="true" />
                  <span>Uso (últimos 7 dias)</span>
                </div>
                {isLoadingStats ? (
                  <p className="mdc-chat-muted">Carregando estatísticas...</p>
                ) : agentStats?.miniDashboard ? (
                  <AgentMiniDashboard stats={agentStats} />
                ) : agentStats ? (
                  <p className="mdc-chat-muted">
                    Estatísticas disponíveis, mas o painel visual não foi retornado pela API.
                  </p>
                ) : (
                  <p className="mdc-chat-muted">Sem dados de uso no período.</p>
                )}
              </div>

              <AgentSpecializationEditor
                agentId={selectedAgent.id}
                getAccessToken={getAccessToken}
                fieldIdPrefix="admin-agents"
                onSaved={() => void loadData()}
              />
            </>
          )}
        </article>
      </div>
    </section>
  );
}
