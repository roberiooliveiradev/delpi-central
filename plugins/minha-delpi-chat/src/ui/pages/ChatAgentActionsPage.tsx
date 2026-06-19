import {
  ArrowLeft,
  Plus,
  RefreshCw,
  Save,
  Settings2,
  Shield,
  Trash2,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  createChatAgentActionProvider,
  deleteChatAgentAction,
  deleteChatAgentActionProvider,
  getChatAgentActionProvider,
  getLatestChatAgentActionProviderImportJob,
  startChatAgentActionProviderImportJob,
  listActionProviders,
  listChatActions,
  listChatAgentActions,
  listChatAgentActionProviders,
  listChatAgentActionTestLogs,
  saveChatAgentActionProvider,
  testChatAgentAction,
  updateChatAgentActionProvider,
  upsertChatAgentAction,
} from "../../data/api/chatApi";
import {
  isBackgroundIndexingJob,
  pollChatActionProviderImportJob,
} from "../../data/chatActionImportPolling";
import { IngestProgressIndicator } from "../components/shared/IngestProgressIndicator";
import type {
  ChatActionCatalogItem,
  ChatExternalActionImportJob,
  ChatActionProvider,
  ChatActionTestLog,
  ChatActionTestResult,
  ChatAgent,
  ChatAgentAction,
  ChatAgentActionProvider,
  ChatAgentPreviewDraft,
} from "../../data/api/chatTypes";
import { useConfirmDialog } from "../components/shared";
import { ChatResourceUsageLink } from "../components/shared/ChatResourceUsageLink";
import { AgentBuilderSwitch } from "../components/workspace/agentBuilder";
import { ChatAgentPreviewWorkspace } from "../components/workspace/ChatAgentPreviewWorkspace";
import { buildChatAgentHref } from "../../navigation/chatRoutes";
import { ActionRoutesSection } from "./agent-actions/ActionRoutesSection";
import type { ActionTestPayload } from "./agent-actions/types";

import "./ChatAgentActionsPage.css";

type ChatAgentActionsPageProps = {
  agent: ChatAgent;
  providerKey?: string | null;
  backLabel?: string;
  onBack: () => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type AuthMode = "none" | "user_token" | "api_key" | "oauth";

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

function buildAgentPreviewDraft(agent: ChatAgent): ChatAgentPreviewDraft {
  return {
    name: agent.name,
    description: agent.description,
    systemPrompt: agent.system_prompt,
    responseStyle: agent.response_style,
    category: agent.category,
    icon: agent.icon,
    maxToolCalls: agent.max_tool_calls,
    requiresConfirmationForWrite: agent.requires_confirmation_for_write,
    metadata: agent.metadata,
  };
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
  if (value === "user_token" || value === "api_key" || value === "oauth") {
    return value;
  }

  return "none";
}

function buildAuthConfig(mode: AuthMode, form: AuthConfigForm): Record<string, unknown> {
  if (mode === "user_token") {
    return {
      source: "current_user",
      headerName: "Authorization",
    };
  }

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
  backLabel = "Voltar ao agente",
  onBack,
  getAccessToken,
}: ChatAgentActionsPageProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
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
  const [importJob, setImportJob] = useState<ChatExternalActionImportJob | null>(null);
  const [backgroundImportJob, setBackgroundImportJob] =
    useState<ChatExternalActionImportJob | null>(null);
  const routesReloadedForImportRef = useRef(false);
  const [isSavingProvider, setIsSavingProvider] = useState(false);
  const [testingActionId, setTestingActionId] = useState<string | null>(null);
  const [testAction, setTestAction] = useState<ChatActionCatalogItem | null>(null);
  const [testResult, setTestResult] = useState<ChatActionTestResult | null>(null);
  const [testLogs, setTestLogs] = useState<ChatActionTestLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<"configure" | "preview">("configure");

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

  const isCreatingNewAction = !selectedProviderKey;

  const buildPreviewDraft = useCallback(
    () => buildAgentPreviewDraft(agent),
    [agent],
  );

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
      setBackgroundImportJob(null);
      return undefined;
    }

    let mounted = true;

    async function refreshBackgroundImportJob() {
      try {
        const latest = await getLatestChatAgentActionProviderImportJob(
          selectedProviderKey,
          { getAccessToken },
        );

        if (!mounted) {
          return;
        }

        if (latest && isBackgroundIndexingJob(latest)) {
          setBackgroundImportJob(latest);
          return;
        }

        setBackgroundImportJob(null);
      } catch {
        if (mounted) {
          setBackgroundImportJob(null);
        }
      }
    }

    void refreshBackgroundImportJob();

    const intervalId = window.setInterval(() => {
      void refreshBackgroundImportJob();
    }, 2000);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, [getAccessToken, selectedProviderKey]);

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

  async function loadActionLogs(action: ChatActionCatalogItem) {
    if (!selectedProviderKey) {
      return;
    }

    const logs = await listChatAgentActionTestLogs(
      agent.id,
      selectedProviderKey,
      action.actionId,
      { getAccessToken },
    );

    setTestLogs(logs);
  }

  async function openTestPanel(action: ChatActionCatalogItem) {
    setTestResult(null);
    setError(null);
    setTestAction(action);

    await loadActionLogs(action);
  }

  async function runActionTest(payload: ActionTestPayload) {
    if (!selectedProviderKey || !testAction) {
      return;
    }

    setTestingActionId(testAction.actionId);
    setTestResult(null);
    setError(null);

    try {
      const result = await testChatAgentAction(
        agent.id,
        selectedProviderKey,
        testAction.actionId,
        payload,
        { getAccessToken },
      );

      setTestResult(result);
      await loadActionLogs(testAction);
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

  function hasActionOverride(action: ChatActionCatalogItem): boolean {
    return configuredActions.some((item) => item.actionId === action.actionId);
  }

  async function toggleProviderEnabled(enabled: boolean) {
    if (!selectedProviderKey || !selectedLink) {
      return;
    }

    setError(null);

    try {
      await saveChatAgentActionProvider(
        agent.id,
        {
          providerKey: selectedProviderKey,
          enabled,
          allowRead: selectedLink.allowRead,
          allowWrite: selectedLink.allowWrite,
          allowAdmin: selectedLink.allowAdmin,
          requiresConfirmationForWrite: selectedLink.requiresConfirmationForWrite,
        },
        { getAccessToken },
      );
      await reloadProviders();
      setSuccessMessage(enabled ? "Action ativada." : "Action desativada.");
    } catch (toggleError) {
      setError(
        toggleError instanceof Error
          ? toggleError.message
          : "Não foi possível alterar o status desta action.",
      );
    }
  }

  async function removeProviderLink() {
    if (!selectedProviderKey || !selectedProvider) {
      return;
    }

    const confirmed = await confirm({
      title: "Excluir action do agente",
      description: `Remover "${selectedProvider.name}" deste agente? As rotas importadas permanecem no catálogo global, mas o vínculo e personalizações serão apagados.`,
      confirmLabel: "Excluir",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setError(null);

    try {
      await deleteChatAgentActionProvider(agent.id, selectedProviderKey, {
        getAccessToken,
      });
      onBack();
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Não foi possível excluir esta action.",
      );
    }
  }

  async function removeActionOverride(action: ChatActionCatalogItem) {
    if (!selectedProviderKey) {
      return;
    }

    if (!hasActionOverride(action)) {
      return;
    }

    const confirmed = await confirm({
      title: "Remover personalização da rota",
      description: `Restaurar "${action.operationId || action.actionId}" ao padrão do provider (habilitada)?`,
      confirmLabel: "Remover",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setError(null);

    try {
      await deleteChatAgentAction(agent.id, selectedProviderKey, action.actionId, {
        getAccessToken,
      });
      await reloadRoutes(selectedProviderKey);
      setSuccessMessage("Personalização da rota removida.");
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "Não foi possível remover a personalização desta rota.",
      );
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
    setImportJob(null);
    routesReloadedForImportRef.current = false;

    try {
      const started = await startChatAgentActionProviderImportJob(
        agent.id,
        selectedProviderKey,
        { getAccessToken },
      );

      setImportJob(started);

      const finished = await pollChatActionProviderImportJob(
        selectedProviderKey,
        started.jobId,
        {
          getAccessToken,
          onJobUpdate: (job) => {
            setImportJob(job);

            if (isBackgroundIndexingJob(job)) {
              setBackgroundImportJob(job);
            }
          },
          onImportActionsReady: async () => {
            routesReloadedForImportRef.current = true;
            await reloadRoutes(selectedProviderKey);
            await reloadProviderDetails(selectedProviderKey);
          },
        },
      );

      if (finished.status === "failed") {
        throw new Error(
          finished.error?.trim() || "Não foi possível concluir a importação das rotas.",
        );
      }

      await reloadProviders();
      await reloadProviderDetails(selectedProviderKey);

      if (!routesReloadedForImportRef.current) {
        await reloadRoutes(selectedProviderKey);
      }

      setSuccessMessage("Rotas atualizadas com sucesso.");
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Não foi possível atualizar as rotas desta action.",
      );
    } finally {
      setIsUpdatingRoutes(false);
      setImportJob(null);
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
      setSuccessMessage("Configuração salva com sucesso.");
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
      <header className="mdc-chat-ws-topbar mdc-chat-agent-actions-page__topbar">
        <div className="mdc-chat-ws-topbar__start">
          <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
            <ArrowLeft size={18} aria-hidden="true" />
            <span>{backLabel}</span>
          </button>
        </div>

        <div className="mdc-chat-ws-topbar__title">
          <span>{selectedProvider?.name ?? "Nova action"}</span>
          <small>{agent.name}</small>
        </div>

        <div className="mdc-chat-ws-topbar__actions">
          {selectedProviderKey ? (
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              disabled={isSavingProvider}
              onClick={() => void saveProviderConfig()}
            >
              <Save size={16} aria-hidden="true" />
              <span>{isSavingProvider ? "Salvando..." : "Salvar configuração"}</span>
            </button>
          ) : null}
        </div>
      </header>

      <div
        className="mdc-chat-agent-actions-page__workspace-tabs"
        role="tablist"
        aria-label="Áreas da configuração de action"
      >
        <button
          type="button"
          role="tab"
          id="mdc-agent-actions-tab-configure"
          aria-selected={workspaceTab === "configure"}
          aria-controls="mdc-agent-actions-panel-configure"
          className={workspaceTab === "configure" ? "is-active" : ""}
          onClick={() => setWorkspaceTab("configure")}
        >
          Configuração
        </button>
        <button
          type="button"
          role="tab"
          id="mdc-agent-actions-tab-preview"
          aria-selected={workspaceTab === "preview"}
          aria-controls="mdc-agent-actions-panel-preview"
          className={workspaceTab === "preview" ? "is-active" : ""}
          onClick={() => setWorkspaceTab("preview")}
        >
          Pré-visualizar
        </button>
      </div>

      <div className="mdc-chat-agent-actions-page__body">
        {workspaceTab === "configure" ? (
        <main
          id="mdc-agent-actions-panel-configure"
          role="tabpanel"
          aria-labelledby="mdc-agent-actions-tab-configure"
          className="mdc-chat-agent-actions-page__editor"
        >
          <div className="mdc-chat-agent-actions-page__panel">
          <header className="mdc-chat-agent-actions-page__headline">
            <h1>{isCreatingNewAction ? "Criar nova ação" : "Editar ação"}</h1>
            <p>
              Configure uma API OpenAPI deste agente: autenticação, schema, rotas
              e política de privacidade.
            </p>
            <ChatResourceUsageLink href={buildChatAgentHref(agent.id)} />
          </header>

          {error ? (
            <div className="mdc-chat-agent-actions-page__error">{error}</div>
          ) : null}

          {successMessage ? (
            <p className="mdc-chat-agent-actions-page__success">{successMessage}</p>
          ) : null}

          {isLoading ? (
            <p className="mdc-chat-muted">Carregando action...</p>
          ) : null}

          {isCreatingNewAction ? (
            <section className="mdc-chat-agent-actions-page__section">
              <div className="mdc-chat-agent-actions-page__section-title">
                <Plus size={18} aria-hidden="true" />
                <div>
                  <h2>Criar nova ação/API</h2>
                  <p>Cadastre uma API OpenAPI diretamente neste agente.</p>
                </div>
              </div>

              <div className="mdc-chat-agent-actions-page__fields">
                <div className="mdc-chat-agent-actions-page__grid">
                  <label className="mdc-chat-ws-field">
                    <span>Nome da API</span>
                    <input
                      value={newProviderName}
                      onChange={(event) => setNewProviderName(event.target.value)}
                      placeholder="API DELPI"
                    />
                  </label>

                  <label className="mdc-chat-ws-field">
                    <span>URL base</span>
                    <input
                      value={newProviderBaseUrl}
                      onChange={(event) => setNewProviderBaseUrl(event.target.value)}
                      placeholder="https://api.exemplo.com.br"
                    />
                  </label>
                </div>

                <div className="mdc-chat-agent-actions-page__grid">
                  <label className="mdc-chat-ws-field">
                    <span>URL OpenAPI</span>
                    <input
                      value={newProviderOpenApiUrl}
                      onChange={(event) => setNewProviderOpenApiUrl(event.target.value)}
                      placeholder="https://api.exemplo.com.br/openapi.json"
                    />
                  </label>

                  <label className="mdc-chat-ws-field">
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

                <label className="mdc-chat-ws-field">
                  <span>Schema OpenAPI JSON</span>
                  <textarea
                    value={newProviderSchema}
                    onChange={(event) => setNewProviderSchema(event.target.value)}
                    placeholder='{"openapi":"3.1.0","info":{"title":"Minha API","version":"1.0.0"},"paths":{}}'
                    rows={12}
                  />
                </label>

                <div className="mdc-chat-agent-actions-page__actions-row">
                  <button
                    type="button"
                    className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                    onClick={() => void createProvider()}
                    disabled={isCreatingProvider}
                  >
                    <Plus size={16} aria-hidden="true" />
                    <span>{isCreatingProvider ? "Criando..." : "Criar nova ação"}</span>
                  </button>
                </div>
              </div>
            </section>
          ) : (
            <>
              {selectedLink ? (
                <section className="mdc-chat-agent-actions-page__section">
                  <div className="mdc-chat-agent-actions-page__provider-toolbar">
                    <AgentBuilderSwitch
                      size="compact"
                      checked={selectedLink.enabled}
                      onChange={(event) => void toggleProviderEnabled(event.target.checked)}
                      label={selectedLink.enabled ? "Action ativa no agente" : "Action desativada no agente"}
                    />
                    <button
                      type="button"
                      className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                      onClick={() => void removeProviderLink()}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                      <span>Excluir action</span>
                    </button>
                  </div>
                </section>
              ) : null}

              <section className="mdc-chat-agent-actions-page__section">
                <div className="mdc-chat-agent-actions-page__section-title">
                  <Settings2 size={18} aria-hidden="true" />
                  <div>
                    <h2>Informações da action</h2>
                    <p>Nome, endpoint base e origem do schema OpenAPI.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__fields">
                  <div className="mdc-chat-agent-actions-page__grid">
                    <label className="mdc-chat-ws-field">
                      <span>Nome da API</span>
                      <input
                        value={providerName}
                        onChange={(event) => setProviderName(event.target.value)}
                      />
                    </label>

                    <label className="mdc-chat-ws-field">
                      <span>URL base</span>
                      <input
                        value={providerBaseUrl}
                        onChange={(event) => setProviderBaseUrl(event.target.value)}
                      />
                    </label>
                  </div>

                  <div className="mdc-chat-agent-actions-page__grid">
                    <label className="mdc-chat-ws-field">
                      <span>URL OpenAPI</span>
                      <input
                        value={providerOpenApiUrl}
                        onChange={(event) => setProviderOpenApiUrl(event.target.value)}
                      />
                    </label>

                    <label className="mdc-chat-ws-field">
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

              <section className="mdc-chat-agent-actions-page__section">
                <div className="mdc-chat-agent-actions-page__section-title">
                  <Shield size={18} aria-hidden="true" />
                  <div>
                    <h2>Autenticação</h2>
                    <p>Como o chat autentica chamadas a esta API.</p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__auth-panel">
                  <span className="mdc-chat-ws-section-head">Tipo de autenticação</span>
                  <div className="mdc-chat-ws-radio-group" role="radiogroup">
                    <label className="mdc-chat-ws-radio-option">
                      <input
                        type="radio"
                        name="action-auth-mode"
                        checked={authMode === "none"}
                        onChange={() => setAuthMode("none")}
                      />
                      <span>Nenhum</span>
                    </label>

                    <label className="mdc-chat-ws-radio-option">
                      <input
                        type="radio"
                        name="action-auth-mode"
                        checked={authMode === "user_token"}
                        onChange={() => setAuthMode("user_token")}
                      />
                      <span>Token do usuário atual</span>
                    </label>

                    <label className="mdc-chat-ws-radio-option">
                      <input
                        type="radio"
                        name="action-auth-mode"
                        checked={authMode === "api_key"}
                        onChange={() => setAuthMode("api_key")}
                      />
                      <span>Chave API</span>
                    </label>

                    <label className="mdc-chat-ws-radio-option">
                      <input
                        type="radio"
                        name="action-auth-mode"
                        checked={authMode === "oauth"}
                        onChange={() => setAuthMode("oauth")}
                      />
                      <span>OAuth</span>
                    </label>
                  </div>

                  {authMode === "user_token" ? (
                    <div className="mdc-chat-agent-actions-page__auth-note">
                      Esta action encaminhará o token do usuário logado para a API.
                      Use este modo para APIs internas da Minha DELPI que validam permissões
                      por usuário.
                    </div>
                  ) : null}

                  {authMode === "api_key" ? (
                    <div className="mdc-chat-agent-actions-page__grid">
                      <label className="mdc-chat-ws-field">
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

                      <label className="mdc-chat-ws-field">
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

                      <label className="mdc-chat-ws-field">
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
                    <div className="mdc-chat-agent-actions-page__fields">
                      <div className="mdc-chat-agent-actions-page__grid">
                        <label className="mdc-chat-ws-field">
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

                        <label className="mdc-chat-ws-field">
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

                      <label className="mdc-chat-ws-field">
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

                      <label className="mdc-chat-ws-field">
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

                      <label className="mdc-chat-ws-field">
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

              <section className="mdc-chat-agent-actions-page__section">
                <div className="mdc-chat-agent-actions-page__section-title">
                  <Zap size={18} aria-hidden="true" />
                  <div>
                    <h2>Schema</h2>
                    <p>
                      Schema OpenAPI salvo. Use Atualizar rotas para reimportar da URL.
                    </p>
                  </div>
                </div>

                <div className="mdc-chat-agent-actions-page__fields">
                  <label className="mdc-chat-ws-field">
                    <span>Schema OpenAPI JSON</span>
                    <textarea
                      value={providerSchemaText}
                      onChange={(event) => setProviderSchemaText(event.target.value)}
                      placeholder="Nenhum schema importado ainda."
                      rows={14}
                      readOnly
                    />
                  </label>

                  <div className="mdc-chat-agent-actions-page__actions-row">
                    <button
                      type="button"
                      className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                      onClick={() => void saveProviderConfig()}
                      disabled={isSavingProvider}
                    >
                      <Save size={16} aria-hidden="true" />
                      <span>
                        {isSavingProvider ? "Salvando..." : "Salvar configuração"}
                      </span>
                    </button>

                    <button
                      type="button"
                      className="mdc-chat-ws-outline-btn"
                      onClick={() => void updateRoutes()}
                      disabled={!selectedProviderKey || isUpdatingRoutes}
                    >
                      <RefreshCw size={16} aria-hidden="true" />
                      <span>{isUpdatingRoutes ? "Atualizando..." : "Atualizar rotas"}</span>
                    </button>
                  </div>

                  <p className="mdc-chat-agent-actions-page__import-hint mdc-chat-muted">
                    As rotas ficam disponíveis logo após o cadastro no catálogo; a indexação
                    semântica continua em segundo plano.
                  </p>

                  {isUpdatingRoutes && importJob ? (
                    <IngestProgressIndicator
                      className="mdc-chat-agent-actions-page__import-progress"
                      label={importJob.phaseLabel}
                      done={importJob.progress.done}
                      total={importJob.progress.total}
                    />
                  ) : null}
                </div>
              </section>

              <ActionRoutesSection
                selectedProvider={selectedProvider}
                selectedLink={selectedLink}
                providerActions={providerActions}
                backgroundImportJob={
                  backgroundImportJob
                    ? {
                        phaseLabel: backgroundImportJob.phaseLabel,
                        progress: backgroundImportJob.progress,
                      }
                    : null
                }
                isLoadingRoutes={isLoadingRoutes}
                testingActionId={testingActionId}
                testAction={testAction}
                testResult={testResult}
                testLogs={testLogs}
                isActionEnabled={isActionEnabled}
                hasActionOverride={hasActionOverride}
                onToggleAction={(action, enabled) =>
                  void toggleAction(action, enabled)
                }
                onRemoveActionOverride={(action) => void removeActionOverride(action)}
                onOpenTestPanel={(action) => void openTestPanel(action)}
                onRunActionTest={runActionTest}
                onCloseTestPanel={() => {
                  setTestAction(null);
                  setTestResult(null);
                  setTestLogs([]);
                }}
                onUpdateProviderPermissions={(patch) =>
                  void updateProviderPermissions(patch)
                }
              />
            </>
          )}
          </div>
        </main>
        ) : (
          <div
            id="mdc-agent-actions-panel-preview"
            role="tabpanel"
            aria-labelledby="mdc-agent-actions-tab-preview"
            className="mdc-chat-agent-actions-page__preview-pane"
          >
            <div className="mdc-chat-agent-actions-page__preview-pane-inner">
              <div className="mdc-chat-agent-actions-page__preview-label">
                <span>Pré-visualizar</span>
                <span className="mdc-chat-agent-actions-page__preview-model">
                  Agente publicado · teste com as actions configuradas
                </span>
              </div>

              <ChatAgentPreviewWorkspace
                agent={agent}
                getAccessToken={getAccessToken}
                buildDraft={buildPreviewDraft}
              />
            </div>
          </div>
        )}
      </div>
      {confirmDialog}
    </section>
  );
}