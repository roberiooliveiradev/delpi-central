import {
  ArrowLeft,
  CheckCircle2,
  DatabaseZap,
  Plus,
  RefreshCw,
  Route,
  Settings2,
  Shield,
  Trash2,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  createChatAgentActionProvider,
  importChatAgentActionProviderSchema,
  listActionProviders,
  listChatActions,
  listChatAgentActions,
  listChatAgentActionProviders,
  saveChatAgentActionProvider,
  upsertChatAgentAction,
} from "../../data/api/chatApi";
import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatAgent,
  ChatAgentAction,
  ChatAgentActionProvider,
} from "../../data/api/chatTypes";

import "./ChatAgentActionsPage.css";

type ChatAgentActionsPageProps = {
  agent: ChatAgent;
  onBack: () => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function createKeyFromName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function getAgentIcebreakers(agent: ChatAgent): string[] {
  const value = agent.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3);
}

export function ChatAgentActionsPage({
  agent,
  onBack,
  getAccessToken,
}: ChatAgentActionsPageProps) {
  const [availableProviders, setAvailableProviders] = useState<ChatActionProvider[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<ChatAgentActionProvider[]>([]);
  const [selectedProviderKey, setSelectedProviderKey] = useState<string | null>(null);
  const [providerActions, setProviderActions] = useState<ChatActionCatalogItem[]>([]);
  const [configuredActions, setConfiguredActions] = useState<ChatAgentAction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);
  const [isImportingProviderKey, setIsImportingProviderKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderBaseUrl, setNewProviderBaseUrl] = useState("");
  const [newProviderOpenApiUrl, setNewProviderOpenApiUrl] = useState("");
  const [newProviderSchema, setNewProviderSchema] = useState("");
  const [isCreatingProvider, setIsCreatingProvider] = useState(false);

  const selectedProvider = useMemo(
    () =>
      configuredProviders.find((provider) => provider.providerKey === selectedProviderKey) ??
      null,
    [configuredProviders, selectedProviderKey],
  );

  const selectedCatalogProvider = useMemo(
    () =>
      availableProviders.find((provider) => provider.providerKey === selectedProviderKey) ??
      null,
    [availableProviders, selectedProviderKey],
  );

  const icebreakers = getAgentIcebreakers(agent);

  async function reloadProviders() {
    const [providers, agentProviders] = await Promise.all([
      listActionProviders({ getAccessToken }),
      listChatAgentActionProviders(agent.id, { getAccessToken }),
    ]);

    setAvailableProviders(providers);
    setConfiguredProviders(agentProviders);

    if (!selectedProviderKey && agentProviders.length > 0) {
      setSelectedProviderKey(agentProviders[0].providerKey);
    }
  }

  async function reloadRoutes(providerKey: string) {
    setIsLoadingRoutes(true);

    try {
      const [actions, overrides] = await Promise.all([
        listChatActions({ providerKey, getAccessToken }),
        listChatAgentActions(agent.id, { getAccessToken }),
      ]);

      setProviderActions(actions);
      setConfiguredActions(
        overrides.filter((item) => item.providerKey === providerKey),
      );
    } finally {
      setIsLoadingRoutes(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const [providers, agentProviders] = await Promise.all([
          listActionProviders({ getAccessToken }),
          listChatAgentActionProviders(agent.id, { getAccessToken }),
        ]);

        if (mounted) {
          setAvailableProviders(providers);
          setConfiguredProviders(agentProviders);

          if (!selectedProviderKey && agentProviders.length > 0) {
            setSelectedProviderKey(agentProviders[0].providerKey);
          }
        }
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Não foi possível carregar as actions do agente.",
          );
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, [agent.id, getAccessToken]);

  useEffect(() => {
    if (!selectedProviderKey) {
      setProviderActions([]);
      setConfiguredActions([]);
      return;
    }

    void reloadRoutes(selectedProviderKey);
  }, [selectedProviderKey]);

  function isActionEnabled(action: ChatActionCatalogItem): boolean {
    const override = configuredActions.find((item) => item.actionId === action.actionId);

    return override?.enabled ?? true;
  }

  async function toggleProvider(provider: ChatActionProvider, enabled: boolean) {
    setError(null);

    await saveChatAgentActionProvider(
      agent.id,
      {
        providerKey: provider.providerKey,
        enabled,
        allowRead: true,
        allowWrite: true,
        allowAdmin: false,
        requiresConfirmationForWrite: true,
      },
      { getAccessToken },
    );

    await reloadProviders();
    setSelectedProviderKey(provider.providerKey);
  }

  async function updateProviderPermissions(
    providerKey: string,
    patch: Partial<
      Pick<
        ChatAgentActionProvider,
        "enabled" | "allowRead" | "allowWrite" | "allowAdmin" | "requiresConfirmationForWrite"
      >
    >,
  ) {
    const current = configuredProviders.find((item) => item.providerKey === providerKey);

    await saveChatAgentActionProvider(
      agent.id,
      {
        providerKey,
        enabled: patch.enabled ?? current?.enabled ?? true,
        allowRead: patch.allowRead ?? current?.allowRead ?? true,
        allowWrite: patch.allowWrite ?? current?.allowWrite ?? true,
        allowAdmin: patch.allowAdmin ?? current?.allowAdmin ?? false,
        requiresConfirmationForWrite:
          patch.requiresConfirmationForWrite ??
          current?.requiresConfirmationForWrite ??
          true,
      },
      { getAccessToken },
    );

    await reloadProviders();
  }

  async function toggleAction(action: ChatActionCatalogItem, enabled: boolean) {
    if (!selectedProviderKey) {
      return;
    }

    await upsertChatAgentAction(
      agent.id,
      {
        providerKey: selectedProviderKey,
        actionId: action.actionId,
        sensitivity: action.sensitivity || "read",
        requiresConfirmation:
          action.sensitivity === "write" ||
          action.sensitivity === "destructive" ||
          action.sensitivity === "sql" ||
          action.sensitivity === "admin",
        enabled,
      },
      { getAccessToken },
    );

    await reloadRoutes(selectedProviderKey);
  }

  async function importProvider(providerKey: string) {
    setIsImportingProviderKey(providerKey);
    setError(null);

    try {
      await importChatAgentActionProviderSchema(agent.id, providerKey, { getAccessToken });
      await reloadProviders();

      if (selectedProviderKey === providerKey) {
        await reloadRoutes(providerKey);
      }
    } catch (importError) {
      setError(
        importError instanceof Error
          ? importError.message
          : "Não foi possível atualizar o schema da API.",
      );
    } finally {
      setIsImportingProviderKey(null);
    }
  }

  async function createProvider() {
    const name = newProviderName.trim();
    const baseUrl = newProviderBaseUrl.trim();
    const openApiUrl = newProviderOpenApiUrl.trim();
    const schemaText = newProviderSchema.trim();

    if (!name || !baseUrl) {
      setError("Informe nome e URL base da API.");
      return;
    }

    let schema: Record<string, unknown> | null = null;

    if (schemaText) {
      try {
        schema = JSON.parse(schemaText) as Record<string, unknown>;
      } catch {
        setError("Schema OpenAPI inválido. Verifique o JSON informado.");
        return;
      }
    }

    setIsCreatingProvider(true);
    setError(null);

    try {
      const providerKey = createKeyFromName(name);

      await createChatAgentActionProvider(
        agent.id,
        {
          providerKey,
          name,
          type: "openapi",
          baseUrl,
          openApiUrl: openApiUrl || null,
          schema,
          authMode: "none",
          enabled: true,
          allowRead: true,
          allowWrite: true,
          allowAdmin: false,
          requiresConfirmationForWrite: true,
        },
        { getAccessToken },
      );

      setNewProviderName("");
      setNewProviderBaseUrl("");
      setNewProviderOpenApiUrl("");
      setNewProviderSchema("");
      setSelectedProviderKey(providerKey);

      await reloadProviders();
      await reloadRoutes(providerKey);
    } catch (createError) {
      setError(
        createError instanceof Error
          ? createError.message
          : "Não foi possível criar a action/API.",
      );
    } finally {
      setIsCreatingProvider(false);
    }
  }

  return (
    <section className="mdc-chat-agent-actions-page">
      <header className="mdc-chat-agent-actions-page__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar</span>
        </button>

        <div>
          <span>{agent.name}</span>
          <small>Editar ações</small>
        </div>

        <button
          type="button"
          className="mdc-chat-agent-actions-page__primary"
          disabled={!selectedProviderKey || isImportingProviderKey !== null}
          onClick={() => {
            if (selectedProviderKey) {
              void importProvider(selectedProviderKey);
            }
          }}
        >
          <RefreshCw size={16} aria-hidden="true" />
          <span>
            {isImportingProviderKey ? "Atualizando..." : "Atualizar"}
          </span>
        </button>
      </header>

      <div className="mdc-chat-agent-actions-page__layout">
        <main className="mdc-chat-agent-actions-page__editor">
          <section className="mdc-chat-agent-actions-page__headline">
            <div className="mdc-chat-agent-actions-page__round-back">
              <button type="button" onClick={onBack} aria-label="Voltar">
                <ArrowLeft size={19} aria-hidden="true" />
              </button>
            </div>

            <h1>Editar ações</h1>
            <p>
              Permita que o agente recupere informações ou realize ações fora do chat.
            </p>
          </section>

          {error ? (
            <div className="mdc-chat-agent-actions-page__error">{error}</div>
          ) : null}

          <section className="mdc-chat-agent-actions-page__block">
            <div className="mdc-chat-agent-actions-page__block-title">
              <Shield size={18} aria-hidden="true" />
              <div>
                <h2>Autenticação</h2>
                <p>Configuração visual inicial. O armazenamento seguro de segredo pode ser conectado depois.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-actions-page__auth-card">
              <span>Tipo de autenticação</span>
              <div>
                <label><input type="radio" checked readOnly /> Nenhum</label>
                <label><input type="radio" readOnly /> Chave API</label>
                <label><input type="radio" readOnly /> OAuth</label>
              </div>
            </div>
          </section>

          <section className="mdc-chat-agent-actions-page__block">
            <div className="mdc-chat-agent-actions-page__block-title">
              <Zap size={18} aria-hidden="true" />
              <div>
                <h2>Actions conectadas</h2>
                <p>Escolha uma API para configurar schema, rotas e permissões.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-actions-page__provider-list">
              {isLoading ? (
                <p className="mdc-chat-muted">Carregando APIs...</p>
              ) : null}

              {availableProviders.map((provider) => {
                const configured = configuredProviders.find(
                  (item) => item.providerKey === provider.providerKey,
                );
                const isEnabled = Boolean(configured?.enabled);
                const isSelected = selectedProviderKey === provider.providerKey;

                return (
                  <article
                    key={provider.providerKey}
                    className={isSelected ? "is-selected" : ""}
                  >
                    <label>
                      <input
                        type="checkbox"
                        checked={isEnabled}
                        onChange={(event) =>
                          void toggleProvider(provider, event.target.checked)
                        }
                      />

                      <span>
                        <strong>{provider.name}</strong>
                        <small>
                          {provider.providerKey}
                          {configured ? ` · ${configured.actionCount} rota(s)` : ""}
                        </small>
                      </span>
                    </label>

                    <button
                      type="button"
                      onClick={() => setSelectedProviderKey(provider.providerKey)}
                    >
                      <Settings2 size={16} aria-hidden="true" />
                      <span>Configurar</span>
                    </button>
                  </article>
                );
              })}

              {availableProviders.length === 0 ? (
                <div className="mdc-chat-agent-actions-page__empty">
                  <DatabaseZap size={24} aria-hidden="true" />
                  <strong>Nenhuma API cadastrada</strong>
                  <p>Crie uma action para começar.</p>
                </div>
              ) : null}
            </div>
          </section>

          <section className="mdc-chat-agent-actions-page__block">
            <div className="mdc-chat-agent-actions-page__block-title">
              <Plus size={18} aria-hidden="true" />
              <div>
                <h2>Criar nova ação</h2>
                <p>Cadastre uma API OpenAPI diretamente neste agente.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-actions-page__create">
              <div className="mdc-chat-agent-actions-page__grid">
                <label>
                  <span>Nome da API</span>
                  <input
                    value={newProviderName}
                    onChange={(event) => setNewProviderName(event.target.value)}
                    placeholder="API DELPI"
                  />
                </label>

                <label>
                  <span>URL base</span>
                  <input
                    value={newProviderBaseUrl}
                    onChange={(event) => setNewProviderBaseUrl(event.target.value)}
                    placeholder="https://api.exemplo.com.br"
                  />
                </label>
              </div>

              <label>
                <span>URL OpenAPI</span>
                <input
                  value={newProviderOpenApiUrl}
                  onChange={(event) => setNewProviderOpenApiUrl(event.target.value)}
                  placeholder="https://api.exemplo.com.br/openapi.json"
                />
              </label>

              <label>
                <span>Schema</span>
                <textarea
                  value={newProviderSchema}
                  onChange={(event) => setNewProviderSchema(event.target.value)}
                  placeholder='{"openapi":"3.1.0","info":{"title":"Minha API","version":"1.0.0"},"paths":{...}}'
                  rows={10}
                />
              </label>

              <button
                type="button"
                onClick={() => void createProvider()}
                disabled={isCreatingProvider}
              >
                <Plus size={16} aria-hidden="true" />
                <span>{isCreatingProvider ? "Criando..." : "Criar nova ação"}</span>
              </button>
            </div>
          </section>

          <section className="mdc-chat-agent-actions-page__block">
            <div className="mdc-chat-agent-actions-page__block-title">
              <Route size={18} aria-hidden="true" />
              <div>
                <h2>Ações disponíveis</h2>
                <p>
                  {selectedProvider
                    ? `${selectedProvider.providerName} · ${providerActions.length} rota(s)`
                    : "Selecione uma API para ver as rotas"}
                </p>
              </div>
            </div>

            {selectedProvider ? (
              <div className="mdc-chat-agent-actions-page__permissions">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedProvider.allowRead}
                    onChange={(event) =>
                      void updateProviderPermissions(selectedProvider.providerKey, {
                        allowRead: event.target.checked,
                      })
                    }
                  />
                  Leitura
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={selectedProvider.allowWrite}
                    onChange={(event) =>
                      void updateProviderPermissions(selectedProvider.providerKey, {
                        allowWrite: event.target.checked,
                      })
                    }
                  />
                  Escrita
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={selectedProvider.allowAdmin}
                    onChange={(event) =>
                      void updateProviderPermissions(selectedProvider.providerKey, {
                        allowAdmin: event.target.checked,
                      })
                    }
                  />
                  Admin
                </label>

                <label>
                  <input
                    type="checkbox"
                    checked={selectedProvider.requiresConfirmationForWrite}
                    onChange={(event) =>
                      void updateProviderPermissions(selectedProvider.providerKey, {
                        requiresConfirmationForWrite: event.target.checked,
                      })
                    }
                  />
                  Confirmar escrita
                </label>
              </div>
            ) : null}

            {!selectedProviderKey ? (
              <div className="mdc-chat-agent-actions-page__empty">
                <DatabaseZap size={24} aria-hidden="true" />
                <strong>Nenhuma API selecionada</strong>
                <p>Escolha uma API conectada para configurar suas rotas.</p>
              </div>
            ) : isLoadingRoutes ? (
              <p className="mdc-chat-muted">Carregando rotas...</p>
            ) : (
              <div className="mdc-chat-agent-actions-page__route-table">
                <div>
                  <span>Nome</span>
                  <span>Método</span>
                  <span>Caminho</span>
                  <span>Status</span>
                </div>

                {providerActions.map((action) => (
                  <article key={action.actionId}>
                    <label>
                      <input
                        type="checkbox"
                        checked={isActionEnabled(action)}
                        onChange={(event) =>
                          void toggleAction(action, event.target.checked)
                        }
                      />
                      <span>{action.operationId || action.actionId}</span>
                    </label>

                    <span>{action.method}</span>
                    <span>{action.path}</span>
                    <small>{action.sensitivity || "read"}</small>
                  </article>
                ))}

                {providerActions.length === 0 ? (
                  <div className="mdc-chat-agent-actions-page__empty">
                    <CheckCircle2 size={24} aria-hidden="true" />
                    <strong>Nenhuma rota importada</strong>
                    <p>Atualize o schema da API para importar rotas OpenAPI.</p>
                  </div>
                ) : null}
              </div>
            )}
          </section>
        </main>

        <aside className="mdc-chat-agent-actions-page__preview">
          <div className="mdc-chat-agent-actions-page__preview-top">
            <strong>Pré-visualizar</strong>
            <button type="button">Modelo</button>
          </div>

          <div className="mdc-chat-agent-actions-page__preview-card">
            <div className="mdc-chat-agent-actions-page__avatar">
              <Zap size={26} aria-hidden="true" />
            </div>

            <h2>{agent.name}</h2>

            <p>
              {agent.description ||
                "Agente configurado com instruções, conhecimento e actions OpenAPI."}
            </p>

            {icebreakers.length > 0 ? (
              <div className="mdc-chat-agent-actions-page__icebreakers">
                {icebreakers.map((icebreaker) => (
                  <button key={icebreaker} type="button">
                    {icebreaker}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="mdc-chat-agent-actions-page__preview-composer">
            <Plus size={18} aria-hidden="true" />
            <span>Pergunte alguma coisa</span>
          </div>
        </aside>
      </div>
    </section>
  );
}
