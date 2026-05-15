import { useEffect, useState } from "react";

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
  listChatAgents,
} from "../../../../data/api/chatApi";
import type {
  AdminExternalActionCatalogItem,
  AdminLlmStatus,
  AdminToolHealthResponse,
} from "../../../../data/api/adminTypes";
import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatAgent,
  ChatAgentAction,
  ChatAgentActionProvider,
  ChatCapabilities,
} from "../../../../data/api/chatTypes";

import "./AdminToolsTab.css";

type AdminToolsTabProps = {
  llmStatus?: AdminLlmStatus | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function AdminToolsTab({ llmStatus, getAccessToken }: AdminToolsTabProps) {
  const [health, setHealth] = useState<AdminToolHealthResponse | null>(null);
  const [actions, setActions] = useState<AdminExternalActionCatalogItem[]>([]);
  const [capabilities, setCapabilities] = useState<ChatCapabilities | null>(null);
  const [chatProviders, setChatProviders] = useState<ChatActionProvider[]>([]);
  const [chatActions, setChatActions] = useState<ChatActionCatalogItem[]>([]);
  const [agents, setAgents] = useState<ChatAgent[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [agentProviders, setAgentProviders] = useState<ChatAgentActionProvider[]>([]);
  const [agentActions, setAgentActions] = useState<ChatAgentAction[]>([]);
  const [isLoadingAgentTools, setIsLoadingAgentTools] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  async function loadAgentTools(agentId: string) {
    setSelectedAgentId(agentId);
    setAgentProviders([]);
    setAgentActions([]);

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

  return (
    <section className="mdc-admin-tools-tab">
      <header className="mdc-admin-tools-tab__hero">
        <div>
          <p className="mdc-chat-eyebrow">Ferramentas</p>
          <h2>Operação de tools e actions</h2>
          <p>
            Monitore providers, actions, saúde operacional e permissões preparadas para o uso seguro pelo chat.
          </p>
        </div>

        <button
          type="button"
          disabled={isLoading}
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

      <div className="mdc-admin-tools-tab__grid">
        <article className="mdc-admin-tools-card">
          <div>
            <p className="mdc-chat-eyebrow">LLM</p>
            <h3>Status do modelo</h3>
          </div>

          <strong>{llmStatus?.provider || llmStatus?.model ? "Configurado" : "Indisponível"}</strong>
          <p>
            {llmStatus?.provider ?? "Provider não informado"} ·{" "}
            {llmStatus?.model ?? "Modelo não informado"}
          </p>
        </article>

        <article className="mdc-admin-tools-card">
          <div>
            <p className="mdc-chat-eyebrow">Health checks</p>
            <h3>Saúde das ferramentas</h3>
          </div>

          {!health || health.items.length === 0 ? (
            <p>Nenhum health check retornado.</p>
          ) : (
            <ul>
              {health.items.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.label}</strong>
                    <small>{item.description}</small>
                  </div>
                  <span className={`is-${item.status}`}>{item.status}</span>
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>

      <article className="mdc-admin-tools-card">
        <div>
          <p className="mdc-chat-eyebrow">Providers OpenAPI</p>
          <h3>Providers cadastrados</h3>
        </div>

        {chatProviders.length === 0 ? (
          <p>Nenhum provider real retornado pelo backend.</p>
        ) : (
          <div className="mdc-admin-tools-tab__providers">
            {chatProviders.map((provider) => (
              <section key={provider.providerKey}>
                <div>
                  <strong>{provider.name}</strong>
                  <small>{provider.providerKey}</small>
                </div>

                <dl>
                  <div>
                    <dt>Tipo</dt>
                    <dd>{provider.type ?? "openapi"}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd className={provider.enabled ? "is-ok" : "is-warning"}>
                      {provider.enabled ? "ativo" : "inativo"}
                    </dd>
                  </div>
                  <div>
                    <dt>Base URL</dt>
                    <dd>{provider.baseUrl ?? "não informado"}</dd>
                  </div>
                </dl>
              </section>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-tools-card">
        <div>
          <p className="mdc-chat-eyebrow">Catálogo real</p>
          <h3>Actions disponíveis</h3>
        </div>

        {chatActions.length === 0 ? (
          <p>Nenhuma action real retornada pelo backend.</p>
        ) : (
          <div className="mdc-admin-tools-tab__actions">
            {chatActions.map((action) => (
              <section key={action.id}>
                <div>
                  <strong>{action.summary ?? action.operationId ?? action.actionId}</strong>
                  <small>{action.actionId}</small>
                </div>

                <dl>
                  <div>
                    <dt>Método</dt>
                    <dd>{action.method ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>Path</dt>
                    <dd>{action.path ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>Risco</dt>
                    <dd>{action.sensitivity ?? "não informado"}</dd>
                  </div>
                </dl>
              </section>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-tools-card">
        <div>
          <p className="mdc-chat-eyebrow">Por agente</p>
          <h3>Providers e actions vinculadas</h3>
        </div>

        <label className="mdc-admin-tools-tab__agent-select">
          <span>Agente</span>
          <select
            value={selectedAgentId}
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
          <div className="mdc-admin-tools-tab__agent-grid">
            <section>
              <h4>Providers do agente</h4>
              {agentProviders.length === 0 ? (
                <p>Nenhum provider vinculado.</p>
              ) : (
                <ul>
                  {agentProviders.map((provider) => (
                    <li key={provider.providerKey}>
                      <div>
                        <strong>{provider.providerName ?? provider.providerKey}</strong>
                        <small>{provider.providerKey}</small>
                      </div>
                      <span className={provider.enabled ? "is-ok" : "is-warning"}>
                        {provider.enabled ? "ativo" : "inativo"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section>
              <h4>Actions do agente</h4>
              {agentActions.length === 0 ? (
                <p>Nenhuma action vinculada.</p>
              ) : (
                <ul>
                  {agentActions.map((action) => (
                    <li key={action.actionId}>
                      <div>
                        <strong>{action.actionId}</strong>
                        <small>{action.providerKey}</small>
                      </div>
                      <span className={action.enabled ? "is-ok" : "is-warning"}>
                        {action.enabled ? "ativa" : "inativa"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        ) : null}
      </article>

      <article className="mdc-admin-tools-card">
        <div>
          <p className="mdc-chat-eyebrow">Actions</p>
          <h3>Catálogo operacional</h3>
        </div>

        {actions.length === 0 ? (
          <p>Nenhuma action externa cadastrada ou disponível.</p>
        ) : (
          <div className="mdc-admin-tools-tab__actions">
            {actions.map((action) => (
              <section key={action.id}>
                <div>
                  <strong>{action.name}</strong>
                  <small>{action.provider}</small>
                </div>

                <dl>
                  <div>
                    <dt>Status</dt>
                    <dd className={`is-${action.status}`}>{action.status}</dd>
                  </div>
                  <div>
                    <dt>Chamadas 24h</dt>
                    <dd>{action.calls24h}</dd>
                  </div>
                  <div>
                    <dt>Última execução</dt>
                    <dd>{action.lastRunAt ?? "Sem registro"}</dd>
                  </div>
                </dl>
              </section>
            ))}
          </div>
        )}
      </article>

      <article className="mdc-admin-tools-card">
        <div>
          <p className="mdc-chat-eyebrow">Permissões</p>
          <h3>Capacidades do usuário atual</h3>
        </div>

        {!capabilities ? (
          <p>Capacidades ainda não carregadas.</p>
        ) : (
          <>
            <div className="mdc-admin-tools-tab__permission-grid">
              <section>
                <strong>{capabilities.canManageTools ? "Sim" : "Não"}</strong>
                <span>Gerencia tools</span>
              </section>

              <section>
                <strong>{capabilities.canUseTools ? "Sim" : "Não"}</strong>
                <span>Usa tools</span>
              </section>

              <section>
                <strong>{capabilities.canManageAgents ? "Sim" : "Não"}</strong>
                <span>Gerencia agentes</span>
              </section>

              <section>
                <strong>{capabilities.canManageOfficialAgents ? "Sim" : "Não"}</strong>
                <span>Agentes oficiais</span>
              </section>
            </div>

            <ul>
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
