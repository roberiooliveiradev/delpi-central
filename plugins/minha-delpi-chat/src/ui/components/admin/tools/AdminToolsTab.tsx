import { useEffect, useState } from "react";

import {
  getAdminToolHealth,
  listAdminExternalActions,
} from "../../../../data/api/adminApi";
import { getChatCapabilities } from "../../../../data/api/chatApi";
import type {
  AdminExternalActionCatalogItem,
  AdminLlmStatus,
  AdminToolHealthResponse,
} from "../../../../data/api/adminTypes";
import type { ChatCapabilities } from "../../../../data/api/chatTypes";

import "./AdminToolsTab.css";

type AdminToolsTabProps = {
  llmStatus?: AdminLlmStatus | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function AdminToolsTab({ llmStatus, getAccessToken }: AdminToolsTabProps) {
  const [health, setHealth] = useState<AdminToolHealthResponse | null>(null);
  const [actions, setActions] = useState<AdminExternalActionCatalogItem[]>([]);
  const [capabilities, setCapabilities] = useState<ChatCapabilities | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadTools() {
    setIsLoading(true);
    setError(null);

    try {
      const [healthResponse, actionsResponse, capabilitiesResponse] = await Promise.all([
        getAdminToolHealth({ getAccessToken }),
        listAdminExternalActions({ getAccessToken }),
        getChatCapabilities({ getAccessToken }),
      ]);

      setHealth(healthResponse);
      setActions(actionsResponse);
      setCapabilities(capabilitiesResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar ferramentas.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadTools();
  }, []);

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
