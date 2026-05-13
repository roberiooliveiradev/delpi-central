import {
  ArrowLeft,
  DatabaseZap,
  Plus,
  RefreshCw,
  Route,
  Settings2,
  Shield,
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
  providerKey?: string | null;
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

function shouldConfirmAction(action: ChatActionCatalogItem): boolean {
  return ["write", "destructive", "sql", "admin"].includes(
    String(action.sensitivity ?? "read"),
  );
}

export function ChatAgentActionsPage({
  agent,
  providerKey,
  onBack,
  getAccessToken,
}: ChatAgentActionsPageProps) {
  const [availableProviders, setAvailableProviders] = useState<ChatActionProvider[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<ChatAgentActionProvider[]>([]);
  const [selectedProviderKey, setSelectedProviderKey] = useState<string | null>(
    providerKey ?? null,
  );
  const [providerActions, setProviderActions] = useState<ChatActionCatalogItem[]>([]);
  const [configuredActions, setConfiguredActions] = useState<ChatAgentAction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);
  const [isUpdatingRoutes, setIsUpdatingRoutes] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderBaseUrl, setNewProviderBaseUrl] = useState("");
  const [newProviderOpenApiUrl, setNewProviderOpenApiUrl] = useState("");
  const [newProviderSchema, setNewProviderSchema] = useState("");
  const [isCreatingProvider, setIsCreatingProvider] = useState(false);

  const selectedProvider = useMemo(
    () =>
      availableProviders.find((provider) => provider.providerKey === selectedProviderKey) ??
      null,
    [availableProviders, selectedProviderKey],
  );

  const selectedLink = useMemo(
    () =>
      configuredProviders.find((provider) => provider.providerKey === selectedProviderKey) ??
      null,
    [configuredProviders, selectedProviderKey],
  );

  const icebreakers = getAgentIcebreakers(agent);
  const isCreatingNewAction = !selectedProviderKey;

  async function reloadProviders() {
    const [providers, agentProviders] = await Promise.all([
      listActionProviders({ getAccessToken }),
      listChatAgentActionProviders(agent.id, { getAccessToken }),
    ]);

    setAvailableProviders(providers);
    setConfiguredProviders(agentProviders);
  }

  async function reloadRoutes(nextProviderKey: string) {
    setIsLoadingRoutes(true);
    setError(null);

    try {
      const [actions, overrides] = await Promise.all([
        listChatActions({ providerKey: nextProviderKey, getAccessToken }),
        listChatAgentActions(agent.id, { getAccessToken }),
      ]);

      setProviderActions(actions);
      setConfiguredActions(
        overrides.filter((item) => item.providerKey === nextProviderKey),
      );
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Não foi possível carregar as rotas desta action.",
      );
    } finally {
      setIsLoadingRoutes(false);
    }
  }

  useEffect(() => {
    let mounted = true;

    async function loadInitialData() {
      setIsLoading(true);
      setError(null);

      try {
        const [providers, agentProviders] = await Promise.all([
          listActionProviders({ getAccessToken }),
          listChatAgentActionProviders(agent.id, { getAccessToken }),
        ]);

        if (!mounted) {
          return;
        }

        setAvailableProviders(providers);
        setConfiguredProviders(agentProviders);

        if (providerKey) {
          setSelectedProviderKey(providerKey);
        }
      } catch (loadError) {
        if (mounted) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Não foi possível carregar a action.",
          );
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialData();

    return () => {
      mounted = false;
    };
  }, [agent.id, getAccessToken, providerKey]);

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

  async function updateProviderPermissions(
    patch: Partial<
      Pick<
        ChatAgentActionProvider,
        "enabled" | "allowRead" | "allowWrite" | "allowAdmin" | "requiresConfirmationForWrite"
      >
    >,
  ) {
    if (!selectedProviderKey) {
      return;
    }

    await saveChatAgentActionProvider(
      agent.id,
      {
        providerKey: selectedProviderKey,
        enabled: patch.enabled ?? selectedLink?.enabled ?? true,
        allowRead: patch.allowRead ?? selectedLink?.allowRead ?? true,
        allowWrite: patch.allowWrite ?? selectedLink?.allowWrite ?? true,
        allowAdmin: patch.allowAdmin ?? selectedLink?.allowAdmin ?? false,
        requiresConfirmationForWrite:
          patch.requiresConfirmationForWrite ??
          selectedLink?.requiresConfirmationForWrite ??
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
        requiresConfirmation: shouldConfirmAction(action),
        enabled,
      },
      { getAccessToken },
    );

    await reloadRoutes(selectedProviderKey);
  }

  async function updateRoutes() {
    if (!selectedProviderKey) {
      setError("Selecione ou crie uma action antes de atualizar rotas.");
      return;
    }

    setIsUpdatingRoutes(true);
    setError(null);

    try {
      await importChatAgentActionProviderSchema(agent.id, selectedProviderKey, {
        getAccessToken,
      });

      await reloadProviders();
      await reloadRoutes(selectedProviderKey);
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Não foi possível atualizar as rotas desta action.",
      );
    } finally {
      setIsUpdatingRoutes(false);
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

    const nextProviderKey = createKeyFromName(name);

    if (!nextProviderKey) {
      setError("Informe um nome válido para gerar a chave da action.");
      return;
    }

    setIsCreatingProvider(true);
    setError(null);

    try {
      await createChatAgentActionProvider(
        agent.id,
        {
          providerKey: nextProviderKey,
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
      setSelectedProviderKey(nextProviderKey);

      await reloadProviders();
      await reloadRoutes(nextProviderKey);
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
          <span>{selectedProvider?.name ?? "Nova action"}</span>
          <small>{agent.name}</small>
        </div>

        <button
          type="button"
          className="mdc-chat-agent-actions-page__primary"
          disabled={!selectedProviderKey || isUpdatingRoutes}
          onClick={() => void updateRoutes()}
        >
          <RefreshCw size={16} aria-hidden="true" />
          <span>{isUpdatingRoutes ? "Atualizando..." : "Atualizar rotas"}</span>
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

            <h1>{isCreatingNewAction ? "Criar nova ação" : "Editar ação"}</h1>
            <p>
              Configure uma API OpenAPI específica deste agente: autenticação,
              schema, rotas disponíveis e política de privacidade.
            </p>
          </section>

          {error ? (
            <div className="mdc-chat-agent-actions-page__error">{error}</div>
          ) : null}

          {isLoading ? (
            <p className="mdc-chat-muted">Carregando action...</p>
          ) : null}

          {isCreatingNewAction ? (
            <section className="mdc-chat-agent-actions-page__block">
              <div className="mdc-chat-agent-actions-page__block-title">
                <Plus size={18} aria-hidden="true" />
                <div>
                  <h2>Criar nova ação/API</h2>
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
                  <span>Schema OpenAPI JSON</span>
                  <textarea
                    value={newProviderSchema}
                    onChange={(event) => setNewProviderSchema(event.target.value)}
                    placeholder='{"openapi":"3.1.0","info":{"title":"Minha API","version":"1.0.0"},"paths":{}}'
                    rows={12}
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
          ) : (
            <>
              <section className="mdc-chat-agent-actions-page__block">
                <div className="mdc-chat-agent-actions-page__block-title">
                  <Shield size={18} aria-hidden="true" />
                  <div>
                    <h2>Autenticação</h2>
                    <p>Configuração da autenticação desta API/action.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__auth-card">
                  <span>Tipo de autenticação</span>
                  <div>
                    <label>
                      <input type="radio" checked readOnly />
                      Nenhum
                    </label>
                    <label>
                      <input type="radio" readOnly />
                      Chave API
                    </label>
                    <label>
                      <input type="radio" readOnly />
                      OAuth
                    </label>
                  </div>

                  <button type="button">
                    <Settings2 size={16} aria-hidden="true" />
                    <span>Configurar autenticação</span>
                  </button>
                </div>
              </section>

              <section className="mdc-chat-agent-actions-page__block">
                <div className="mdc-chat-agent-actions-page__block-title">
                  <Zap size={18} aria-hidden="true" />
                  <div>
                    <h2>Schema</h2>
                    <p>Origem OpenAPI usada para importar e atualizar rotas.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__create">
                  <div className="mdc-chat-agent-actions-page__grid">
                    <label>
                      <span>URL base</span>
                      <input value={selectedProvider?.baseUrl ?? ""} readOnly />
                    </label>

                    <label>
                      <span>URL OpenAPI</span>
                      <input value={selectedProvider?.openApiUrl ?? ""} readOnly />
                    </label>
                  </div>

                  <label>
                    <span>Schema OpenAPI JSON</span>
                    <textarea
                      value={
                        selectedProvider?.openApiUrl
                          ? `// Schema importado de ${selectedProvider.openApiUrl}\n// Use "Atualizar rotas" para reimportar o OpenAPI desta action.`
                          : "// Schema cadastrado nesta action.\n// Use \"Atualizar rotas\" para reprocessar as rotas disponíveis."
                      }
                      readOnly
                      rows={10}
                    />
                  </label>

                  <button
                    type="button"
                    onClick={() => void updateRoutes()}
                    disabled={!selectedProviderKey || isUpdatingRoutes}
                  >
                    <RefreshCw size={16} aria-hidden="true" />
                    <span>{isUpdatingRoutes ? "Atualizando..." : "Atualizar rotas"}</span>
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
                        ? `${selectedProvider.name} · ${providerActions.length} rota(s)`
                        : "Action não encontrada"}
                    </p>
                  </div>
                </div>

                {selectedLink ? (
                  <div className="mdc-chat-agent-actions-page__permissions">
                    <label>
                      <input
                        type="checkbox"
                        checked={selectedLink.allowRead}
                        onChange={(event) =>
                          void updateProviderPermissions({
                            allowRead: event.target.checked,
                          })
                        }
                      />
                      Leitura
                    </label>

                    <label>
                      <input
                        type="checkbox"
                        checked={selectedLink.allowWrite}
                        onChange={(event) =>
                          void updateProviderPermissions({
                            allowWrite: event.target.checked,
                          })
                        }
                      />
                      Escrita
                    </label>

                    <label>
                      <input
                        type="checkbox"
                        checked={selectedLink.allowAdmin}
                        onChange={(event) =>
                          void updateProviderPermissions({
                            allowAdmin: event.target.checked,
                          })
                        }
                      />
                      Admin
                    </label>

                    <label>
                      <input
                        type="checkbox"
                        checked={selectedLink.requiresConfirmationForWrite}
                        onChange={(event) =>
                          void updateProviderPermissions({
                            requiresConfirmationForWrite: event.target.checked,
                          })
                        }
                      />
                      Confirmar escrita
                    </label>
                  </div>
                ) : null}

                {isLoadingRoutes ? (
                  <p className="mdc-chat-muted">Carregando rotas...</p>
                ) : providerActions.length > 0 ? (
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

                        <span>{action.method ?? "-"}</span>
                        <span>{action.path ?? "-"}</span>
                        <small>{action.sensitivity || "read"}</small>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="mdc-chat-agent-actions-page__empty">
                    <DatabaseZap size={24} aria-hidden="true" />
                    <strong>Nenhuma rota importada</strong>
                    <p>Use “Atualizar rotas” para importar as rotas desta action.</p>
                  </div>
                )}
              </section>

              <section className="mdc-chat-agent-actions-page__block">
                <div className="mdc-chat-agent-actions-page__block-title">
                  <Shield size={18} aria-hidden="true" />
                  <div>
                    <h2>Política de privacidade</h2>
                    <p>URL exibida para usuários quando esta action acessar serviços externos.</p>
                  </div>
                </div>

                <label>
                  <span>URL da política</span>
                  <input placeholder="https://app.example.com/privacy" />
                </label>
              </section>
            </>
          )}
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
