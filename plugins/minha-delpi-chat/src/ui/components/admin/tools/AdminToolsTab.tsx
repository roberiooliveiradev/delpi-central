import { useEffect, useMemo, useState } from "react";

import {
  getAdminToolHealth,
  listAdminExternalActions,
} from "../../../../data/api/adminApi";
import {
  getChatCapabilities,
  listActionProviders,
  listChatActions,
  listChatAgentActions,
  listChatAgentActionProviders,
  listChatAgentActionTestLogs,
  listChatAgents,
} from "../../../../data/api/chatApi";
import type {
  AdminExternalActionCatalogItem,
  AdminLlmStatus,
  AdminRbacSummary,
  AdminToolHealthResponse,
} from "../../../../data/api/adminTypes";
import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatAgent,
  ChatAgentAction,
  ChatAgentActionProvider,
  ChatActionTestLog,
  ChatCapabilities,
} from "../../../../data/api/chatTypes";

import { ChatIntelligenceSettingsPanel } from "../metrics-tab/ChatIntelligenceSettingsPanel";
import { ToolsSummaryStrip } from "./ToolsSummaryStrip";
import { computeToolsSummary } from "./toolsSummary";

import "./AdminToolsTab.css";

function healthStatusClass(status: string): string {
  if (status === "ok") {
    return "mdc-admin-badge--success";
  }

  if (status === "warning") {
    return "mdc-admin-badge--muted";
  }

  return "mdc-admin-badge--danger";
}

type AdminToolsTabProps = {
  llmStatus?: AdminLlmStatus | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  rbac?: AdminRbacSummary | null;
  /** tools = health/actions; intelligence = só políticas do pipeline */
  view?: "tools" | "intelligence";
};

export function AdminToolsTab({
  llmStatus,
  getAccessToken,
  rbac,
  view = "tools",
}: AdminToolsTabProps) {
  const [health, setHealth] = useState<AdminToolHealthResponse | null>(null);
  const [actions, setActions] = useState<AdminExternalActionCatalogItem[]>([]);
  const [capabilities, setCapabilities] = useState<ChatCapabilities | null>(null);
  const [chatProviders, setChatProviders] = useState<ChatActionProvider[]>([]);
  const [chatActions, setChatActions] = useState<ChatActionCatalogItem[]>([]);
  const [agents, setAgents] = useState<ChatAgent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [agentProviders, setAgentProviders] = useState<ChatAgentActionProvider[]>([]);
  const [agentActions, setAgentActions] = useState<ChatAgentAction[]>([]);
  const [selectedAgentActionKey, setSelectedAgentActionKey] = useState("");
  const [actionLogs, setActionLogs] = useState<ChatActionTestLog[]>([]);
  const [isLoadingAgentTools, setIsLoadingAgentTools] = useState(false);
  const [isLoadingActionLogs, setIsLoadingActionLogs] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canManageTools = Boolean(rbac?.capabilities.canManageTools);
  const canUseTools = Boolean(rbac?.capabilities.canUseTools);

  const toolsSummary = useMemo(
    () => computeToolsSummary(llmStatus, health, actions.length, chatActions.length),
    [llmStatus, health, actions.length, chatActions.length],
  );

  async function loadTools() {
    setIsLoading(true);
    setError(null);

    try {
      const [
        healthResponse,
        actionsResponse,
        capabilitiesResponse,
        providersResponse,
        chatActionsResponse,
        agentsResponse,
      ] = await Promise.all([
        getAdminToolHealth({ getAccessToken }),
        listAdminExternalActions({ getAccessToken }),
        getChatCapabilities({ getAccessToken }),
        listActionProviders({ getAccessToken }),
        listChatActions({ getAccessToken }),
        listChatAgents({ getAccessToken }),
      ]);

      setHealth(healthResponse);
      setActions(actionsResponse);
      setCapabilities(capabilitiesResponse);
      setChatProviders(providersResponse);
      setChatActions(chatActionsResponse);
      setAgents(agentsResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar ferramentas.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTools();
  }, []);

  async function loadActionLogs(value: string) {
    setSelectedAgentActionKey(value);
    setActionLogs([]);

    if (!selectedAgentId || !value) {
      return;
    }

    const [providerKey, actionId] = value.split("::");

    if (!providerKey || !actionId) {
      return;
    }

    setIsLoadingActionLogs(true);
    setError(null);

    try {
      const logs = await listChatAgentActionTestLogs(
        selectedAgentId,
        providerKey,
        actionId,
        { getAccessToken },
      );

      setActionLogs(logs);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao carregar logs recentes da action.",
      );
    } finally {
      setIsLoadingActionLogs(false);
    }
  }

  async function loadAgentTools(agentId: string) {
    setSelectedAgentId(agentId);
    setAgentProviders([]);
    setAgentActions([]);
    setSelectedAgentActionKey("");
    setActionLogs([]);

    if (!agentId) {
      return;
    }

    setIsLoadingAgentTools(true);
    setError(null);

    try {
      const [providersResponse, actionsResponse] = await Promise.all([
        listChatAgentActionProviders(agentId, { getAccessToken }),
        listChatAgentActions(agentId, { getAccessToken }),
      ]);

      setAgentProviders(providersResponse);
      setAgentActions(actionsResponse);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Erro ao carregar ferramentas do agente.",
      );
    } finally {
      setIsLoadingAgentTools(false);
    }
  }

  if (view === "intelligence") {
    return (
      <section className="mdc-admin-tools-tab mdc-admin-tools-tab--intelligence">
        <header className="mdc-admin-tab-header">
          <div className="mdc-admin-page-header">
            <p className="mdc-chat-eyebrow">Plataforma</p>
            <h2>Inteligência do chat</h2>
            <p>
              Políticas globais do pipeline (roteamento, RAG, tools). Métricas ficam em Qualidade.
            </p>
          </div>
        </header>
        <ChatIntelligenceSettingsPanel getAccessToken={getAccessToken} />
      </section>
    );
  }

  return (
    <section className="mdc-admin-tools-tab">
      <header className="mdc-admin-tools-tab__toolbar mdc-admin-tab-header">
        <div className="mdc-admin-page-header">
          <p className="mdc-chat-eyebrow">Plataforma</p>
          <h2>Ferramentas e integrações</h2>
          <p>Providers LLM, saúde operacional e catálogo de actions por agente.</p>
        </div>

        <ToolsSummaryStrip summary={toolsSummary} />

        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          disabled={isLoading || !canUseTools}
          title={
            canUseTools
              ? "Atualizar ferramentas"
              : "Você não tem permissão para visualizar/usar ferramentas."
          }
          onClick={() => {
            void loadTools();
          }}
        >
          {isLoading ? "Atualizando..." : "Atualizar"}
        </button>
      </header>

      {error ? (
        <div className="mdc-admin-tools-tab__error" role="alert">
          {error}
        </div>
      ) : null}

      <article className="mdc-admin-panel">
        <h3 className="mdc-admin-tools-tab__section-title">Saúde das ferramentas</h3>

        {!health || health.items.length === 0 ? (
          <p className="mdc-chat-muted">Nenhum health check retornado.</p>
        ) : (
          <div className="mdc-admin-entity-list mdc-admin-tools-tab__entity-list">
            {health.items.map((item) => (
              <article key={item.id} className="mdc-admin-entity-row">
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>{item.label}</strong>
                    <span className={`mdc-admin-badge ${healthStatusClass(item.status)}`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="mdc-admin-entity-row__detail">{item.description}</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-panel">
        <header className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Providers OpenAPI</p>
          <h2>Providers cadastrados</h2>
        </header>

        {chatProviders.length === 0 ? (
          <p className="mdc-chat-muted">Nenhum provider real retornado pelo backend.</p>
        ) : (
          <div className="mdc-admin-entity-list mdc-admin-tools-tab__entity-list">
            {chatProviders.map((provider) => (
              <article key={provider.providerKey} className="mdc-admin-entity-row">
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>{provider.name}</strong>
                    <span
                      className={`mdc-admin-badge ${
                        provider.enabled ? "mdc-admin-badge--success" : "mdc-admin-badge--muted"
                      }`}
                    >
                      {provider.enabled ? "ativo" : "inativo"}
                    </span>
                  </div>
                  <div className="mdc-admin-entity-row__meta">
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {provider.type ?? "openapi"}
                    </span>
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {provider.providerKey}
                    </span>
                  </div>
                  <p className="mdc-admin-entity-row__detail">
                    {provider.baseUrl ?? "Base URL não informada"}
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-panel">
        <header className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Catálogo real</p>
          <h2>Actions disponíveis</h2>
          <p className="mdc-chat-muted">
            Rotas OpenAPI registradas no backend ({chatActions.length} action(s)).
          </p>
        </header>

        {chatActions.length === 0 ? (
          <p className="mdc-chat-muted">Nenhuma action real retornada pelo backend.</p>
        ) : (
          <div className="mdc-admin-entity-list mdc-admin-tools-tab__entity-list mdc-admin-tools-tab__entity-list--tall">
            {chatActions.map((action) => (
              <article key={action.id} className="mdc-admin-entity-row">
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>
                      {action.summary ?? action.operationId ?? action.actionId}
                    </strong>
                  </div>
                  <div className="mdc-admin-entity-row__meta">
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {action.method ?? "—"}
                    </span>
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {action.sensitivity ?? "—"}
                    </span>
                  </div>
                  <p className="mdc-admin-entity-row__detail">{action.path ?? "—"}</p>
                  <small className="mdc-admin-entity-row__detail">{action.actionId}</small>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-panel">
        <header className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Por agente</p>
          <h2>Providers e actions vinculadas</h2>
        </header>

        {!canManageTools ? (
          <div className="mdc-admin-tools-tab__error" role="note">
            Você não tem permissão para gerenciar ferramentas por agente.
          </div>
        ) : null}

        <label className="mdc-admin-field mdc-admin-tools-tab__agent-select">
          <span>Agente</span>
          <select
            value={selectedAgentId}
            disabled={!canManageTools}
            onChange={(event) => {
              void loadAgentTools(event.target.value);
            }}
          >
            <option value="">Selecione um agente</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </label>

        {isLoadingAgentTools ? <p>Carregando tools do agente...</p> : null}

        {selectedAgentId && !isLoadingAgentTools ? (
          <>
            <div className="mdc-admin-tools-tab__agent-grid">
              <section>
                <h4>Providers do agente</h4>
                {agentProviders.length === 0 ? (
                  <p className="mdc-chat-muted">Nenhum provider vinculado.</p>
                ) : (
                  <div className="mdc-admin-entity-list">
                    {agentProviders.map((provider) => (
                      <article key={provider.providerKey} className="mdc-admin-entity-row">
                        <div className="mdc-admin-entity-row__body">
                          <div className="mdc-admin-entity-row__title-line">
                            <strong>{provider.providerName ?? provider.providerKey}</strong>
                            <span
                              className={`mdc-admin-badge ${
                                provider.enabled
                                  ? "mdc-admin-badge--success"
                                  : "mdc-admin-badge--muted"
                              }`}
                            >
                              {provider.enabled ? "ativo" : "inativo"}
                            </span>
                          </div>
                          <small className="mdc-admin-entity-row__detail">
                            {provider.providerKey}
                          </small>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h4>Actions do agente</h4>
                {agentActions.length === 0 ? (
                  <p className="mdc-chat-muted">Nenhuma action vinculada.</p>
                ) : (
                  <div className="mdc-admin-entity-list">
                    {agentActions.map((action) => (
                      <article
                        key={`${action.providerKey}:${action.actionId}`}
                        className="mdc-admin-entity-row"
                      >
                        <div className="mdc-admin-entity-row__body">
                          <div className="mdc-admin-entity-row__title-line">
                            <strong>{action.actionId}</strong>
                            <span
                              className={`mdc-admin-badge ${
                                action.enabled
                                  ? "mdc-admin-badge--success"
                                  : "mdc-admin-badge--muted"
                              }`}
                            >
                              {action.enabled ? "ativa" : "inativa"}
                            </span>
                          </div>
                          <small className="mdc-admin-entity-row__detail">
                            {action.providerKey}
                          </small>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </section>
            </div>

            <section className="mdc-admin-tools-tab__logs">
              <div>
                <h4>Logs recentes por action</h4>
                <p>Consulte os últimos testes registrados para uma action vinculada ao agente.</p>
              </div>

              <label className="mdc-admin-field mdc-admin-tools-tab__agent-select">
                <span>Action</span>
                <select
                  value={selectedAgentActionKey}
                  disabled={!canManageTools || agentActions.length === 0}
                  onChange={(event) => {
                    void loadActionLogs(event.target.value);
                  }}
                >
                  <option value="">Selecione uma action</option>
                  {agentActions.map((action) => (
                    <option
                      key={`${action.providerKey}:${action.actionId}`}
                      value={`${action.providerKey}::${action.actionId}`}
                    >
                      {action.providerKey} · {action.actionId}
                    </option>
                  ))}
                </select>
              </label>

              {isLoadingActionLogs ? <p>Carregando logs...</p> : null}

              {!isLoadingActionLogs && selectedAgentActionKey && actionLogs.length === 0 ? (
                <p>Nenhum log recente retornado para esta action.</p>
              ) : null}

              {actionLogs.length > 0 ? (
                <div className="mdc-admin-entity-list mdc-admin-tools-tab__entity-list">
                  {actionLogs.map((log) => (
                    <article key={log.id} className="mdc-admin-entity-row">
                      <div className="mdc-admin-entity-row__body">
                        <div className="mdc-admin-entity-row__title-line">
                          <strong>
                            {log.providerKey} · {log.actionId}
                          </strong>
                          <span
                            className={`mdc-admin-badge ${
                              log.ok ? "mdc-admin-badge--success" : "mdc-admin-badge--danger"
                            }`}
                          >
                            {log.ok ? "OK" : "Erro"} · {log.statusCode ?? "—"}
                          </span>
                        </div>
                        <p className="mdc-admin-entity-row__detail">
                          {log.durationMs}ms ·{" "}
                          {log.createdAt
                            ? new Date(log.createdAt).toLocaleString("pt-BR")
                            : "sem data"}
                        </p>
                        {log.errorMessage ? (
                          <p className="mdc-admin-entity-row__detail">{log.errorMessage}</p>
                        ) : null}
                      </div>
                    </article>
                  ))}
                </div>
              ) : null}
            </section>
          </>
        ) : null}
      </article>

      <article className="mdc-admin-panel">
        <header className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Actions</p>
          <h2>Catálogo operacional</h2>
          <p className="mdc-chat-muted">Uso e status das actions externas no período recente.</p>
        </header>

        {actions.length === 0 ? (
          <p className="mdc-chat-muted">Nenhuma action externa cadastrada ou disponível.</p>
        ) : (
          <div className="mdc-admin-entity-list mdc-admin-tools-tab__entity-list">
            {actions.map((action) => (
              <article key={action.id} className="mdc-admin-entity-row">
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>{action.name}</strong>
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {action.status}
                    </span>
                  </div>
                  <div className="mdc-admin-entity-row__meta">
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {action.provider}
                    </span>
                    <span className="mdc-admin-badge mdc-admin-badge--muted">
                      {action.calls24h} chamada(s) / 24h
                    </span>
                  </div>
                  <p className="mdc-admin-entity-row__detail">
                    Última execução: {action.lastRunAt ?? "sem registro"}
                  </p>
                </div>
              </article>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-panel">
        <header className="mdc-admin-panel__intro">
          <p className="mdc-chat-eyebrow">Permissões</p>
          <h2>Capacidades do usuário atual</h2>
        </header>

        {!capabilities ? (
          <p className="mdc-chat-muted">Capacidades ainda não carregadas.</p>
        ) : (
          <>
            <div className="mdc-admin-tools-tab__permission-grid">
              <article>
                <strong>{capabilities.canManageTools ? "Sim" : "Não"}</strong>
                <span>Gerencia tools</span>
              </article>

              <article>
                <strong>{capabilities.canUseTools ? "Sim" : "Não"}</strong>
                <span>Usa tools</span>
              </article>

              <article>
                <strong>{capabilities.canManageAgents ? "Sim" : "Não"}</strong>
                <span>Gerencia agentes</span>
              </article>

              <article>
                <strong>{capabilities.canManageOfficialAgents ? "Sim" : "Não"}</strong>
                <span>Agentes oficiais</span>
              </article>
            </div>

            <ul className="mdc-admin-tools-tab__capabilities-list">
              <li>
                <strong>Permissões detectadas</strong>
                <small>
                  {capabilities.permissions.length > 0
                    ? capabilities.permissions.join(", ")
                    : "Nenhuma permissão explícita retornada."}
                </small>
              </li>
              <li>
                <strong>Superadmin</strong>
                <small>{capabilities.isSuperadmin ? "Sim" : "Não"}</small>
              </li>
              <li>
                <strong>Escopo por agente</strong>
                <small>
                  Providers e actions continuam vinculados ao agente e às permissões do usuário.
                </small>
              </li>
            </ul>
          </>
        )}
      </article>

    </section>
  );
}
