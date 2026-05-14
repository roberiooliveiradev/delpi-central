import {
  ArrowLeft,
  DatabaseZap,
  Plus,
  RefreshCw,
  Route,
  Save,
  Settings2,
  Shield,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  createChatAgentActionProvider,
  getChatAgentActionProvider,
  importChatAgentActionProviderSchema,
  listActionProviders,
  listChatActions,
  listChatAgentActions,
  listChatAgentActionProviders,
  saveChatAgentActionProvider,
  updateChatAgentActionProvider,
  upsertChatAgentAction,
  testChatAgentAction,
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

type AuthMode = "none" | "api_key" | "oauth";

type AuthConfigForm = {
  apiKey: string;
  headerName: string;
  scheme: "basic" | "bearer" | "custom";
  clientId: string;
  clientSecret: string;
  authorizationUrl: string;
  tokenUrl: string;
  scope: string;
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

function stringifySchema(schema: Record<string, unknown> | null | undefined): string {
  if (!schema) {
    return "";
  }

  try {
    return JSON.stringify(schema, null, 2);
  } catch {
    return "";
  }
}

function normalizeAuthMode(value: string | null | undefined): AuthMode {
  if (value === "api_key" || value === "oauth") {
    return value;
  }

  return "none";
}

function buildAuthConfig(mode: AuthMode, form: AuthConfigForm): Record<string, unknown> {
  if (mode === "api_key") {
    return {
      apiKey: form.apiKey,
      headerName: form.headerName || "Authorization",
      scheme: form.scheme,
    };
  }

  if (mode === "oauth") {
    return {
      clientId: form.clientId,
      clientSecret: form.clientSecret,
      authorizationUrl: form.authorizationUrl,
      tokenUrl: form.tokenUrl,
      scope: form.scope,
    };
  }

  return {};
}

function readAuthConfig(provider: ChatActionProvider | null): AuthConfigForm {
  const config = provider?.authConfig ?? {};

  return {
    apiKey: typeof config.apiKey === "string" ? config.apiKey : "",
    headerName: typeof config.headerName === "string" ? config.headerName : "Authorization",
    scheme:
      config.scheme === "basic" || config.scheme === "custom"
        ? config.scheme
        : "bearer",
    clientId: typeof config.clientId === "string" ? config.clientId : "",
    clientSecret: typeof config.clientSecret === "string" ? config.clientSecret : "",
    authorizationUrl:
      typeof config.authorizationUrl === "string" ? config.authorizationUrl : "",
    tokenUrl: typeof config.tokenUrl === "string" ? config.tokenUrl : "",
    scope: typeof config.scope === "string" ? config.scope : "",
  };
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
  const [providerDetails, setProviderDetails] = useState<ChatActionProvider | null>(null);
  const [providerActions, setProviderActions] = useState<ChatActionCatalogItem[]>([]);
  const [configuredActions, setConfiguredActions] = useState<ChatAgentAction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);
  const [isUpdatingRoutes, setIsUpdatingRoutes] = useState(false);
  const [isSavingProvider, setIsSavingProvider] = useState(false);
  const [testingActionId, setTestingActionId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderBaseUrl, setNewProviderBaseUrl] = useState("");
  const [newProviderOpenApiUrl, setNewProviderOpenApiUrl] = useState("");
  const [newProviderSchema, setNewProviderSchema] = useState("");
  const [newProviderPrivacyPolicyUrl, setNewProviderPrivacyPolicyUrl] = useState("");
  const [isCreatingProvider, setIsCreatingProvider] = useState(false);

  const [providerName, setProviderName] = useState("");
  const [providerBaseUrl, setProviderBaseUrl] = useState("");
  const [providerOpenApiUrl, setProviderOpenApiUrl] = useState("");
  const [providerPrivacyPolicyUrl, setProviderPrivacyPolicyUrl] = useState("");
  const [providerSchemaText, setProviderSchemaText] = useState("");
  const [authMode, setAuthMode] = useState<AuthMode>("none");
  const [authConfig, setAuthConfig] = useState<AuthConfigForm>({
    apiKey: "",
    headerName: "Authorization",
    scheme: "bearer",
    clientId: "",
    clientSecret: "",
    authorizationUrl: "",
    tokenUrl: "",
    scope: "",
  });

  const selectedProvider = useMemo(
    () =>
      providerDetails ??
      availableProviders.find((provider) => provider.providerKey === selectedProviderKey) ??
      null,
    [availableProviders, providerDetails, selectedProviderKey],
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

  async function reloadProviderDetails(nextProviderKey: string) {
    const details = await getChatAgentActionProvider(agent.id, nextProviderKey, {
      getAccessToken,
    });

    setProviderDetails(details);
    setProviderName(details.name ?? "");
    setProviderBaseUrl(details.baseUrl ?? "");
    setProviderOpenApiUrl(details.openApiUrl ?? "");
    setProviderPrivacyPolicyUrl(details.privacyPolicyUrl ?? "");
    setProviderSchemaText(stringifySchema(details.latestSchema));
    setAuthMode(normalizeAuthMode(details.authMode));
    setAuthConfig(readAuthConfig(details));
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
      setProviderDetails(null);
      setProviderActions([]);
      setConfiguredActions([]);
      return;
    }

    void reloadProviderDetails(selectedProviderKey);
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

  async function testAction(action: ChatActionCatalogItem) {
    if (!selectedProviderKey) {
      return;
    }

    setTestingActionId(action.actionId);
    setTestResult(null);
    setError(null);

    try {
      const pathParams: Record<string, string> = {};
      const placeholders = Array.from(action.path.matchAll(/\{([^}]+)\}/g));

      for (const match of placeholders) {
        const key = match[1];
        const value = window.prompt(`Valor para {${key}}`, "");

        if (value === null) {
          setTestingActionId(null);
          return;
        }

        pathParams[key] = value;
      }

      let body: unknown = undefined;

      if (!["GET", "HEAD"].includes(String(action.method).toUpperCase())) {
        const rawBody = window.prompt(
          "Body JSON para teste",
          "{}",
        );

        if (rawBody === null) {
          setTestingActionId(null);
          return;
        }

        body = rawBody.trim() ? JSON.parse(rawBody) : undefined;
      }

      const result = await testChatAgentAction(
        agent.id,
        selectedProviderKey,
        action.actionId,
        {
          pathParams,
          query: {},
          body,
        },
        { getAccessToken },
      );

      setTestResult(
        [
          result.ok ? "Teste executado com sucesso." : "Teste retornou erro.",
          `Status: ${result.statusCode ?? "-"}`,
          `Duração: ${result.durationMs}ms`,
          `URL: ${result.url}`,
          "",
          result.errorMessage ? `Erro: ${result.errorMessage}` : "",
          result.responsePreview || "",
        ]
          .filter(Boolean)
          .join("\n"),
      );
    } catch (testError) {
      setError(
        testError instanceof Error
          ? testError.message
          : "Não foi possível testar esta rota.",
      );
    } finally {
      setTestingActionId(null);
    }
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
      await reloadProviderDetails(selectedProviderKey);
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

  async function saveProviderConfig() {
    if (!selectedProviderKey) {
      return;
    }

    if (!providerName.trim() || !providerBaseUrl.trim()) {
      setError("Informe nome e URL base da API.");
      return;
    }

    setIsSavingProvider(true);
    setError(null);

    try {
      const updated = await updateChatAgentActionProvider(
        agent.id,
        selectedProviderKey,
        {
          name: providerName.trim(),
          baseUrl: providerBaseUrl.trim(),
          openApiUrl: providerOpenApiUrl.trim() || null,
          privacyPolicyUrl: providerPrivacyPolicyUrl.trim() || null,
          authMode,
          authConfig: buildAuthConfig(authMode, authConfig),
        },
        { getAccessToken },
      );

      setProviderDetails(updated);
      await reloadProviders();
      await reloadProviderDetails(selectedProviderKey);
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Não foi possível salvar a configuração desta action.",
      );
    } finally {
      setIsSavingProvider(false);
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
          privacyPolicyUrl: newProviderPrivacyPolicyUrl.trim() || null,
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
      setNewProviderPrivacyPolicyUrl("");
      setSelectedProviderKey(nextProviderKey);

      await reloadProviders();
      await reloadProviderDetails(nextProviderKey);
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

                <div className="mdc-chat-agent-actions-page__grid">
                  <label>
                    <span>URL OpenAPI</span>
                    <input
                      value={newProviderOpenApiUrl}
                      onChange={(event) => setNewProviderOpenApiUrl(event.target.value)}
                      placeholder="https://api.exemplo.com.br/openapi.json"
                    />
                  </label>

                  <label>
                    <span>Política de privacidade</span>
                    <input
                      value={newProviderPrivacyPolicyUrl}
                      onChange={(event) =>
                        setNewProviderPrivacyPolicyUrl(event.target.value)
                      }
                      placeholder="https://app.example.com/privacy"
                    />
                  </label>
                </div>

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
                  <Settings2 size={18} aria-hidden="true" />
                  <div>
                    <h2>Informações da action</h2>
                    <p>Nome, endpoint base e origem do schema OpenAPI.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__create">
                  <div className="mdc-chat-agent-actions-page__grid">
                    <label>
                      <span>Nome da API</span>
                      <input
                        value={providerName}
                        onChange={(event) => setProviderName(event.target.value)}
                      />
                    </label>

                    <label>
                      <span>URL base</span>
                      <input
                        value={providerBaseUrl}
                        onChange={(event) => setProviderBaseUrl(event.target.value)}
                      />
                    </label>
                  </div>

                  <div className="mdc-chat-agent-actions-page__grid">
                    <label>
                      <span>URL OpenAPI</span>
                      <input
                        value={providerOpenApiUrl}
                        onChange={(event) => setProviderOpenApiUrl(event.target.value)}
                      />
                    </label>

                    <label>
                      <span>Política de privacidade</span>
                      <input
                        value={providerPrivacyPolicyUrl}
                        onChange={(event) =>
                          setProviderPrivacyPolicyUrl(event.target.value)
                        }
                        placeholder="https://app.example.com/privacy"
                      />
                    </label>
                  </div>
                </div>
              </section>

              <section className="mdc-chat-agent-actions-page__block">
                <div className="mdc-chat-agent-actions-page__block-title">
                  <Shield size={18} aria-hidden="true" />
                  <div>
                    <h2>Autenticação</h2>
                    <p>Configuração real salva junto desta API/action.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__auth-card">
                  <span>Tipo de autenticação</span>
                  <div>
                    <label>
                      <input
                        type="radio"
                        checked={authMode === "none"}
                        onChange={() => setAuthMode("none")}
                      />
                      Nenhum
                    </label>
                    <label>
                      <input
                        type="radio"
                        checked={authMode === "api_key"}
                        onChange={() => setAuthMode("api_key")}
                      />
                      Chave API
                    </label>
                    <label>
                      <input
                        type="radio"
                        checked={authMode === "oauth"}
                        onChange={() => setAuthMode("oauth")}
                      />
                      OAuth
                    </label>
                  </div>

                  {authMode === "api_key" ? (
                    <div className="mdc-chat-agent-actions-page__grid">
                      <label>
                        <span>Chave API</span>
                        <input
                          value={authConfig.apiKey}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              apiKey: event.target.value,
                            }))
                          }
                          placeholder="[OCULTO]"
                          type="password"
                        />
                      </label>

                      <label>
                        <span>Nome do cabeçalho</span>
                        <input
                          value={authConfig.headerName}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              headerName: event.target.value,
                            }))
                          }
                          placeholder="Authorization"
                        />
                      </label>

                      <label>
                        <span>Formato</span>
                        <select
                          value={authConfig.scheme}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              scheme: event.target.value as AuthConfigForm["scheme"],
                            }))
                          }
                        >
                          <option value="bearer">Bearer</option>
                          <option value="basic">Basic</option>
                          <option value="custom">Personalizado</option>
                        </select>
                      </label>
                    </div>
                  ) : null}

                  {authMode === "oauth" ? (
                    <div className="mdc-chat-agent-actions-page__create">
                      <div className="mdc-chat-agent-actions-page__grid">
                        <label>
                          <span>ID do cliente</span>
                          <input
                            value={authConfig.clientId}
                            onChange={(event) =>
                              setAuthConfig((current) => ({
                                ...current,
                                clientId: event.target.value,
                              }))
                            }
                          />
                        </label>

                        <label>
                          <span>Segredo do cliente</span>
                          <input
                            value={authConfig.clientSecret}
                            onChange={(event) =>
                              setAuthConfig((current) => ({
                                ...current,
                                clientSecret: event.target.value,
                              }))
                            }
                            type="password"
                          />
                        </label>
                      </div>

                      <label>
                        <span>URL de autorização</span>
                        <input
                          value={authConfig.authorizationUrl}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              authorizationUrl: event.target.value,
                            }))
                          }
                        />
                      </label>

                      <label>
                        <span>Token URL</span>
                        <input
                          value={authConfig.tokenUrl}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              tokenUrl: event.target.value,
                            }))
                          }
                        />
                      </label>

                      <label>
                        <span>Escopo</span>
                        <input
                          value={authConfig.scope}
                          onChange={(event) =>
                            setAuthConfig((current) => ({
                              ...current,
                              scope: event.target.value,
                            }))
                          }
                        />
                      </label>
                    </div>
                  ) : null}
                </div>
              </section>

              <section className="mdc-chat-agent-actions-page__block">
                <div className="mdc-chat-agent-actions-page__block-title">
                  <Zap size={18} aria-hidden="true" />
                  <div>
                    <h2>Schema</h2>
                    <p>
                      Schema OpenAPI salvo. Use Atualizar rotas para reimportar da URL.
                    </p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__create">
                  <label>
                    <span>Schema OpenAPI JSON</span>
                    <textarea
                      value={providerSchemaText}
                      onChange={(event) => setProviderSchemaText(event.target.value)}
                      placeholder="Nenhum schema importado ainda."
                      rows={14}
                      readOnly
                    />
                  </label>

                  <div className="mdc-chat-agent-actions-page__inline-actions">
                    <button
                      type="button"
                      onClick={() => void saveProviderConfig()}
                      disabled={isSavingProvider}
                    >
                      <Save size={16} aria-hidden="true" />
                      <span>{isSavingProvider ? "Salvando..." : "Salvar configuração"}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => void updateRoutes()}
                      disabled={!selectedProviderKey || isUpdatingRoutes}
                    >
                      <RefreshCw size={16} aria-hidden="true" />
                      <span>{isUpdatingRoutes ? "Atualizando..." : "Atualizar rotas"}</span>
                    </button>
                  </div>
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
                      <span>Teste</span>
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
                        <button
                          type="button"
                          onClick={() => void testAction(action)}
                          disabled={testingActionId === action.actionId}
                        >
                          {testingActionId === action.actionId ? "Testando..." : "Testar"}
                        </button>
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
