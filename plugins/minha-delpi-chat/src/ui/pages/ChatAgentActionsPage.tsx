import {
  ArrowLeft,
  CheckCircle2,
  DatabaseZap,
  Plus,
  RefreshCw,
  Route,
  Settings2,
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

  async function reloadProviders() {
    const [providers, agentProviders] = await Promise.all([
      listActionProviders({ getAccessToken }),
      listChatAgentActionProviders(agent.id, { getAccessToken }),
    ]);

    setAvailableProviders(providers);
    setConfiguredProviders(agentProviders);
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
          <span>Voltar para configurar agente</span>
        </button>

        <div>
          <Zap size={18} aria-hidden="true" />
          <span>Actions</span>
        </div>
      </header>

      <main className="mdc-chat-agent-actions-page__main">
        <section className="mdc-chat-agent-actions-page__hero">
          <p className="mdc-chat-eyebrow">Agente</p>
          <h1>Actions de {agent.name}</h1>
          <p>
            Cadastre APIs OpenAPI, atualize schemas e escolha quais rotas este agente
            pode usar.
          </p>
        </section>

        {error ? (
          <div className="mdc-chat-agent-actions-page__error">{error}</div>
        ) : null}

        <section className="mdc-chat-agent-actions-page__create">
          <div>
            <h2>Criar nova ação/API</h2>
            <p>
              Informe uma URL OpenAPI ou cole o schema JSON. As rotas importadas
              ficarão vinculadas ao agente.
            </p>
          </div>

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
            <span>Schema OpenAPI JSON</span>
            <textarea
              value={newProviderSchema}
              onChange={(event) => setNewProviderSchema(event.target.value)}
              placeholder='{"openapi":"3.1.0","info":{"title":"Minha API","version":"1.0.0"},"paths":{...}}'
              rows={8}
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
        </section>

        <section className="mdc-chat-agent-actions-page__layout">
          <div className="mdc-chat-agent-actions-page__providers">
            <div className="mdc-chat-agent-actions-page__section-title">
              <h2>APIs conectadas</h2>
              <p>{configuredProviders.length} API(s) configurada(s) neste agente</p>
            </div>

            {isLoading ? (
              <p className="mdc-chat-muted">Carregando APIs...</p>
            ) : null}

            {availableProviders.map((provider) => {
              const configured = configuredProviders.find(
                (item) => item.providerKey === provider.providerKey,
              );
              const isEnabled = Boolean(configured?.enabled);

              return (
                <article
                  key={provider.providerKey}
                  className={
                    selectedProviderKey === provider.providerKey
                      ? "mdc-chat-agent-actions-page__provider mdc-chat-agent-actions-page__provider--active"
                      : "mdc-chat-agent-actions-page__provider"
                  }
                >
                  <div className="mdc-chat-agent-actions-page__provider-main">
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
                          {provider.providerKey} · {provider.type}
                          {configured ? ` · ${configured.actionCount} rota(s)` : ""}
                        </small>
                      </span>
                    </label>

                    <button
                      type="button"
                      onClick={() => setSelectedProviderKey(provider.providerKey)}
                    >
                      <Route size={16} aria-hidden="true" />
                      <span>Rotas</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => void importProvider(provider.providerKey)}
                      disabled={isImportingProviderKey === provider.providerKey}
                    >
                      <RefreshCw size={16} aria-hidden="true" />
                      <span>
                        {isImportingProviderKey === provider.providerKey
                          ? "Atualizando..."
                          : "Atualizar schema"}
                      </span>
                    </button>
                  </div>

                  {configured ? (
                    <div className="mdc-chat-agent-actions-page__permissions">
                      <label>
                        <input
                          type="checkbox"
                          checked={configured.allowRead}
                          onChange={(event) =>
                            void updateProviderPermissions(provider.providerKey, {
                              allowRead: event.target.checked,
                            })
                          }
                        />
                        Leitura
                      </label>

                      <label>
                        <input
                          type="checkbox"
                          checked={configured.allowWrite}
                          onChange={(event) =>
                            void updateProviderPermissions(provider.providerKey, {
                              allowWrite: event.target.checked,
                            })
                          }
                        />
                        Escrita
                      </label>

                      <label>
                        <input
                          type="checkbox"
                          checked={configured.allowAdmin}
                          onChange={(event) =>
                            void updateProviderPermissions(provider.providerKey, {
                              allowAdmin: event.target.checked,
                            })
                          }
                        />
                        Admin
                      </label>

                      <label>
                        <input
                          type="checkbox"
                          checked={configured.requiresConfirmationForWrite}
                          onChange={(event) =>
                            void updateProviderPermissions(provider.providerKey, {
                              requiresConfirmationForWrite: event.target.checked,
                            })
                          }
                        />
                        Confirmar escrita
                      </label>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>

          <div className="mdc-chat-agent-actions-page__routes">
            <div className="mdc-chat-agent-actions-page__section-title">
              <h2>Rotas</h2>
              <p>
                {selectedProvider
                  ? `${selectedProvider.providerName} · ${providerActions.length} rota(s)`
                  : "Selecione uma API para ver as rotas"}
              </p>
            </div>

            {!selectedProviderKey ? (
              <div className="mdc-chat-agent-actions-page__empty">
                <DatabaseZap size={24} aria-hidden="true" />
                <strong>Nenhuma API selecionada</strong>
                <p>Escolha uma API conectada para configurar suas rotas.</p>
              </div>
            ) : isLoadingRoutes ? (
              <p className="mdc-chat-muted">Carregando rotas...</p>
            ) : (
              <div className="mdc-chat-agent-actions-page__route-list">
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

                      <span>
                        <strong>
                          {action.method} {action.path}
                        </strong>
                        <small>
                          {action.summary || action.operationId}
                          {action.sensitivity ? ` · ${action.sensitivity}` : ""}
                        </small>
                      </span>
                    </label>

                    <Settings2 size={15} aria-hidden="true" />
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
          </div>
        </section>
      </main>
    </section>
  );
}
