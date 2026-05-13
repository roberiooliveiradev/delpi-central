import {
  ArrowLeft,
  Bot,
  Check,
  FileText,
  Plus,
  Sparkles,
  Trash2,
  Upload,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  createAgentTextSource,
  createChatAgentActionProvider,
  deleteChatSource,
  listActionProviders,
  listAgentSources,
  listChatActions,
  listChatAgentActions,
  listChatAgentActionProviders,
  upsertChatAgentAction,
  saveChatAgentActionProvider,
  uploadAgentSource,
} from "../../data/api/chatApi";
import type {
  ChatActionCatalogItem,
  ChatActionProvider,
  ChatAgent,
  ChatAgentAction,
  ChatAgentActionProvider,
  ChatWorkspaceSource,
} from "../../data/api/chatTypes";

import "./ChatAgentBuilderPage.css";

type AgentPayload = {
  key?: string | null;
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
};

type AgentUpdatePayload = Partial<AgentPayload> & {
  enabled?: boolean;
};

type ChatAgentBuilderPageProps = {
  agent?: ChatAgent | null;
  onBack: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function createKeyFromName(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function getAgentIcebreakers(agent?: ChatAgent | null): string[] {
  const value = agent?.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getMetadataRecord(
  metadata: Record<string, unknown> | null | undefined,
  key: string,
): Record<string, unknown> {
  const value = metadata?.[key];

  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }

  return value as Record<string, unknown>;
}

function getMetadataStringArray(
  metadata: Record<string, unknown> | null | undefined,
  key: string,
): string[] {
  const value = metadata?.[key];

  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

export function ChatAgentBuilderPage({
  agent,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  getAccessToken,
}: ChatAgentBuilderPageProps) {
  const isEditing = Boolean(agent);

  const [key, setKey] = useState(agent?.key ?? "");
  const [name, setName] = useState(agent?.name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [visibility, setVisibility] = useState(agent?.visibility === "public" ? "public" : "private");
  const [category, setCategory] = useState(agent?.category ?? "");
  const [icon, setIcon] = useState(agent?.icon ?? "bot");
  const [responseStyle, setResponseStyle] = useState(agent?.response_style ?? "objetivo");
  const [icebreakers, setIcebreakers] = useState<string[]>(
    getAgentIcebreakers(agent).length > 0 ? getAgentIcebreakers(agent) : [""],
  );

  const capabilities = getMetadataRecord(agent?.metadata, "capabilities");

  const [capActions, setCapActions] = useState(
    typeof capabilities.actions === "boolean" ? capabilities.actions : true,
  );
  const [capFiles, setCapFiles] = useState(
    typeof capabilities.files === "boolean" ? capabilities.files : true,
  );
  const [capCanvas, setCapCanvas] = useState(
    typeof capabilities.canvas === "boolean" ? capabilities.canvas : true,
  );

  const [allowedActions] = useState<string[]>(
    getMetadataStringArray(agent?.metadata, "allowed_actions"),
  );

  const [availableProviders, setAvailableProviders] = useState<ChatActionProvider[]>([]);
  const [configuredProviders, setConfiguredProviders] = useState<ChatAgentActionProvider[]>([]);
  const [selectedProviderKey, setSelectedProviderKey] = useState<string | null>(null);
  const [providerActions, setProviderActions] = useState<ChatActionCatalogItem[]>([]);
  const [configuredActions, setConfiguredActions] = useState<ChatAgentAction[]>([]);
  const [isLoadingProviderActions, setIsLoadingProviderActions] = useState(false);
  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderBaseUrl, setNewProviderBaseUrl] = useState("");
  const [newProviderOpenApiUrl, setNewProviderOpenApiUrl] = useState("");
  const [newProviderSchema, setNewProviderSchema] = useState("");
  const [isCreatingProvider, setIsCreatingProvider] = useState(false);
  const [agentSources, setAgentSources] = useState<ChatWorkspaceSource[]>([]);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [isSavingSource, setIsSavingSource] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);


  useEffect(() => {
    let isMounted = true;

    async function loadProviders() {
      try {
        const [providers, agentProviders] = await Promise.all([
          listActionProviders({ getAccessToken }),
          agent
            ? listChatAgentActionProviders(agent.id, { getAccessToken })
            : Promise.resolve([]),
        ]);

        if (isMounted) {
          setAvailableProviders(providers);
          setConfiguredProviders(agentProviders);
        }
      } catch (error) {
        if (isMounted) {
          setLocalError(
            error instanceof Error
              ? error.message
              : "Não foi possível carregar as APIs do agente.",
          );
        }
      }
    }

    void loadProviders();

    return () => {
      isMounted = false;
    };
  }, [agent?.id, getAccessToken]);


  useEffect(() => {
    let isMounted = true;

    async function loadProviderActions() {
      if (!agent || !selectedProviderKey) {
        setProviderActions([]);
        setConfiguredActions([]);
        return;
      }

      setIsLoadingProviderActions(true);

      try {
        const [actions, overrides] = await Promise.all([
          listChatActions({ providerKey: selectedProviderKey, getAccessToken }),
          listChatAgentActions(agent.id, { getAccessToken }),
        ]);

        if (isMounted) {
          setProviderActions(actions);
          setConfiguredActions(
            overrides.filter((item) => item.providerKey === selectedProviderKey),
          );
        }
      } catch (error) {
        if (isMounted) {
          setLocalError(
            error instanceof Error
              ? error.message
              : "Não foi possível carregar as rotas da API.",
          );
        }
      } finally {
        if (isMounted) {
          setIsLoadingProviderActions(false);
        }
      }
    }

    void loadProviderActions();

    return () => {
      isMounted = false;
    };
  }, [agent?.id, selectedProviderKey, getAccessToken]);

  useEffect(() => {
    let isMounted = true;

    async function loadSources() {
      if (!agent) {
        setAgentSources([]);
        return;
      }

      const sources = await listAgentSources(agent.id, { getAccessToken });

      if (isMounted) {
        setAgentSources(sources);
      }
    }

    void loadSources();

    return () => {
      isMounted = false;
    };
  }, [agent?.id, getAccessToken]);



  async function createAgentProviderFromForm() {
    if (!agent) {
      setLocalError("Salve o agente antes de criar actions.");
      return;
    }

    const name = newProviderName.trim();
    const baseUrl = newProviderBaseUrl.trim();
    const openApiUrl = newProviderOpenApiUrl.trim();
    const schemaText = newProviderSchema.trim();

    if (!name || !baseUrl) {
      setLocalError("Informe nome e URL base da API.");
      return;
    }

    let schema: Record<string, unknown> | null = null;

    if (schemaText) {
      try {
        schema = JSON.parse(schemaText) as Record<string, unknown>;
      } catch {
        setLocalError("Schema OpenAPI inválido. Verifique o JSON informado.");
        return;
      }
    }

    const providerKey = createKeyFromName(name);

    setIsCreatingProvider(true);
    setLocalError(null);

    try {
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

      setAvailableProviders(await listActionProviders({ getAccessToken }));
      setConfiguredProviders(await listChatAgentActionProviders(agent.id, { getAccessToken }));
    } finally {
      setIsCreatingProvider(false);
    }
  }

  async function toggleAgentProvider(provider: ChatActionProvider, enabled: boolean) {
    if (!agent) {
      setLocalError("Salve o agente antes de conectar APIs.");
      return;
    }

    await saveChatAgentActionProvider(
      agent.id,
      {
        providerKey: provider.providerKey,
        enabled,
        allowRead: true,
        allowWrite: false,
        allowAdmin: false,
        requiresConfirmationForWrite: true,
      },
      { getAccessToken },
    );

    setConfiguredProviders(await listChatAgentActionProviders(agent.id, { getAccessToken }));
  }

  async function updateAgentProviderPermissions(
    providerKey: string,
    patch: Partial<Pick<ChatAgentActionProvider, "allowRead" | "allowWrite" | "allowAdmin" | "requiresConfirmationForWrite" | "enabled">>,
  ) {
    if (!agent) {
      return;
    }

    const current = configuredProviders.find((item) => item.providerKey === providerKey);

    await saveChatAgentActionProvider(
      agent.id,
      {
        providerKey,
        enabled: patch.enabled ?? current?.enabled ?? true,
        allowRead: patch.allowRead ?? current?.allowRead ?? true,
        allowWrite: patch.allowWrite ?? current?.allowWrite ?? false,
        allowAdmin: patch.allowAdmin ?? current?.allowAdmin ?? false,
        requiresConfirmationForWrite:
          patch.requiresConfirmationForWrite ??
          current?.requiresConfirmationForWrite ??
          true,
      },
      { getAccessToken },
    );

    setConfiguredProviders(await listChatAgentActionProviders(agent.id, { getAccessToken }));
  }


  function isActionEnabledByOverride(action: ChatActionCatalogItem): boolean {
    const override = configuredActions.find((item) => item.actionId === action.actionId);

    return override?.enabled ?? true;
  }

  async function toggleProviderAction(action: ChatActionCatalogItem, enabled: boolean) {
    if (!agent || !selectedProviderKey) {
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

    const overrides = await listChatAgentActions(agent.id, { getAccessToken });
    setConfiguredActions(
      overrides.filter((item) => item.providerKey === selectedProviderKey),
    );
  }

  async function uploadAgentKnowledgeFile(file: File | null | undefined) {
    if (!agent || !file) {
      return;
    }

    setIsSavingSource(true);

    try {
      await uploadAgentSource(agent.id, file, { getAccessToken });
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    } finally {
      setIsSavingSource(false);
    }
  }

  async function createAgentKnowledgeNote() {
    if (!agent || !sourceContent.trim()) {
      return;
    }

    setIsSavingSource(true);

    try {
      await createAgentTextSource(
        agent.id,
        {
          title: sourceTitle.trim() || "Nota do agente",
          content: sourceContent.trim(),
          metadata: {
            source: "agent_note",
          },
        },
        { getAccessToken },
      );

      setSourceTitle("");
      setSourceContent("");
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    } finally {
      setIsSavingSource(false);
    }
  }

  async function removeAgentSource(sourceId: string) {
    await deleteChatSource(sourceId, { getAccessToken });

    if (agent) {
      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));
    }
  }

  const normalizedIcebreakers = useMemo(
    () => icebreakers.map((item) => item.trim()).filter(Boolean).slice(0, 8),
    [icebreakers],
  );

  function updateIcebreaker(index: number, value: string) {
    setIcebreakers((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? value : item)),
    );
  }

  function removeIcebreaker(index: number) {
    setIcebreakers((current) => {
      const next = current.filter((_, itemIndex) => itemIndex !== index);
      return next.length > 0 ? next : [""];
    });
  }

  function addIcebreaker() {
    setIcebreakers((current) => {
      if (current.length >= 8) {
        return current;
      }

      return [...current, ""];
    });
  }

  async function submitForm() {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do agente.");
      return;
    }

    const normalizedKey = key.trim() || createKeyFromName(normalizedName);

    if (!normalizedKey) {
      setLocalError("Informe uma chave válida para o agente.");
      return;
    }

    const metadata = {
      ...(agent?.metadata ?? {}),
      icebreakers: normalizedIcebreakers,
      allowed_actions: allowedActions,
      capabilities: {
        ...capabilities,
        actions: capActions,
        files: capFiles,
        canvas: capCanvas,
      },
    };

    const payload: AgentPayload = {
      key: normalizedKey,
      name: normalizedName,
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      visibility,
      category: category.trim() || null,
      icon: icon.trim() || null,
      responseStyle,
      metadata,
    };

    setIsSaving(true);
    setLocalError(null);

    try {
      if (agent) {
        const updated = await onUpdateAgent?.(agent.id, payload);

        if (updated) {
          onSelectAgent?.(updated.key);
          onBack();
        }

        return;
      }

      const created = await onCreateAgent?.(payload);

      if (created) {
        onSelectAgent?.(created.key);
        onBack();
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteCurrentAgent() {
    if (!agent) {
      return;
    }

    const confirmed = window.confirm(`Excluir o agente "${agent.name}"?`);

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteAgent?.(agent.id);

    if (deleted) {
      onSelectAgent?.(null);
      onBack();
    }
  }

  return (
    <section className="mdc-chat-agent-builder" aria-label="Configurar agente">
      <header className="mdc-chat-agent-builder__topbar">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={18} aria-hidden="true" />
          <span>Voltar para agentes</span>
        </button>

        <div>
          <span>{isEditing ? "Configurar agente" : "Criar agente"}</span>
          {isEditing ? <small>Última edição salva no agente</small> : null}
        </div>

        <div className="mdc-chat-agent-builder__topbar-actions">
          {agent ? (
            <button
              type="button"
              className="mdc-chat-agent-builder__danger"
              onClick={() => void deleteCurrentAgent()}
            >
              <Trash2 size={17} aria-hidden="true" />
              <span>Excluir</span>
            </button>
          ) : null}

          <button
            type="button"
            className="mdc-chat-agent-builder__primary"
            disabled={isSaving}
            onClick={() => void submitForm()}
          >
            <Check size={17} aria-hidden="true" />
            <span>{isSaving ? "Salvando..." : isEditing ? "Atualizar" : "Criar"}</span>
          </button>
        </div>
      </header>

      <div className="mdc-chat-agent-builder__layout">
        <form
          className="mdc-chat-agent-builder__form"
          onSubmit={(event) => {
            event.preventDefault();
            void submitForm();
          }}
        >
          <div className="mdc-chat-agent-builder__switch">
            <span>Criar</span>
            <strong>Configurar</strong>
          </div>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Bot size={18} aria-hidden="true" />
              <div>
                <h2>Identidade</h2>
                <p>Nome, descrição e aparência do especialista.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__grid">
              <label>
                <span>Nome</span>
                <input
                  value={name}
                  maxLength={120}
                  onChange={(event) => {
                    const nextName = event.target.value;
                    setName(nextName);

                    if (!isEditing && !key.trim()) {
                      setKey(createKeyFromName(nextName));
                    }
                  }}
                  placeholder="Especialista em Produtos DELPI"
                />
              </label>

              <label>
                <span>Chave</span>
                <input
                  value={key}
                  maxLength={80}
                  disabled={isEditing}
                  onChange={(event) => setKey(event.target.value)}
                  placeholder="especialista-produtos"
                />
              </label>
            </div>

            <label>
              <span>Descrição</span>
              <textarea
                value={description}
                rows={3}
                maxLength={900}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique quando este agente deve ser usado..."
              />
            </label>

            <div className="mdc-chat-agent-builder__grid mdc-chat-agent-builder__grid--three">
              <label>
                <span>Visibilidade</span>
                <select
                  value={visibility}
                  onChange={(event) => setVisibility(event.target.value)}
                >
                  <option value="private">Privado</option>
                  <option value="public">Público interno</option>
                </select>
              </label>

              <label>
                <span>Categoria</span>
                <input
                  value={category}
                  maxLength={80}
                  onChange={(event) => setCategory(event.target.value)}
                  placeholder="Produtos"
                />
              </label>

              <label>
                <span>Ícone</span>
                <input
                  value={icon}
                  maxLength={60}
                  onChange={(event) => setIcon(event.target.value)}
                  placeholder="bot"
                />
              </label>
            </div>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <FileText size={18} aria-hidden="true" />
              <div>
                <h2>Instruções</h2>
                <p>Defina comportamento, regras, limites e estilo de resposta.</p>
              </div>
            </div>

            <label>
              <span>Instruções do agente</span>
              <textarea
                className="mdc-chat-agent-builder__prompt"
                value={systemPrompt}
                maxLength={12000}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Defina comportamento, tom, limites, regras e ações permitidas..."
              />
              <small>
                Ao editar, preencha apenas se quiser substituir as instruções atuais.
              </small>
            </label>

            <label>
              <span>Estilo de resposta</span>
              <select
                value={responseStyle}
                onChange={(event) => setResponseStyle(event.target.value)}
              >
                <option value="objetivo">Objetivo</option>
                <option value="tecnico">Técnico</option>
                <option value="executivo">Executivo</option>
                <option value="detalhado">Detalhado</option>
              </select>
            </label>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Sparkles size={18} aria-hidden="true" />
              <div>
                <h2>Quebra-gelos</h2>
                <p>Perguntas iniciais opcionais exibidas na home do agente.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__icebreakers">
              {icebreakers.map((icebreaker, index) => (
                <div key={`${index}-${icebreakers.length}`}>
                  <input
                    value={icebreaker}
                    maxLength={180}
                    onChange={(event) => updateIcebreaker(index, event.target.value)}
                    placeholder="Ex.: Quero verificar um desenho."
                  />

                  <button
                    type="button"
                    onClick={() => removeIcebreaker(index)}
                    aria-label="Remover quebra-gelo"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              ))}

              <button
                type="button"
                className="mdc-chat-agent-builder__secondary"
                onClick={addIcebreaker}
                disabled={icebreakers.length >= 8}
              >
                <Plus size={16} aria-hidden="true" />
                <span>Adicionar quebra-gelo</span>
              </button>
            </div>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <Zap size={18} aria-hidden="true" />
              <div>
                <h2>Recursos e actions</h2>
                <p>Preparado no front; o backend conectará catálogo e permissões.</p>
              </div>
            </div>

            <div className="mdc-chat-agent-builder__toggles">
              <label>
                <input
                  type="checkbox"
                  checked={capActions}
                  onChange={(event) => setCapActions(event.target.checked)}
                />
                <span>Permitir actions</span>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={capFiles}
                  onChange={(event) => setCapFiles(event.target.checked)}
                />
                <span>Permitir documentos/fontes</span>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={capCanvas}
                  onChange={(event) => setCapCanvas(event.target.checked)}
                />
                <span>Permitir lousa/canvas</span>
              </label>
            </div>

            <section className="mdc-chat-agent-builder__section">
              <div className="mdc-chat-agent-builder__section-title">
                <Zap size={18} aria-hidden="true" />
                <div>
                  <h2>APIs e actions</h2>
                  <p>
                    Conecte uma ou mais APIs OpenAPI. O agente poderá usar as rotas disponíveis
                    desses providers.
                  </p>
                </div>
              </div>

              {agent ? (
                <>
                  <div className="mdc-chat-agent-builder__action-create">
                    <h3>Criar nova ação/API</h3>
                    <p>Cadastre uma API OpenAPI diretamente neste agente. As rotas importadas ficarão disponíveis para ele.</p>

                    <div className="mdc-chat-agent-builder__grid">
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
                        rows={8}
                        placeholder='{"openapi":"3.1.0","info":{"title":"Minha API","version":"1.0.0"},"paths":{...}}'
                      />
                    </label>

                    <button
                      type="button"
                      className="mdc-chat-agent-builder__secondary"
                      disabled={isCreatingProvider}
                      onClick={() => void createAgentProviderFromForm()}
                    >
                      <Plus size={16} aria-hidden="true" />
                      <span>{isCreatingProvider ? "Criando..." : "Criar nova ação"}</span>
                    </button>
                  </div>

                  <div className="mdc-chat-agent-builder__provider-list">
                  {availableProviders.map((provider) => {
                    const configured = configuredProviders.find(
                      (item) => item.providerKey === provider.providerKey,
                    );

                    const isEnabled = Boolean(configured?.enabled);

                    return (
                      <article key={provider.providerKey}>
                        <label>
                          <input
                            type="checkbox"
                            checked={isEnabled}
                            onChange={(event) =>
                              void toggleAgentProvider(provider, event.target.checked)
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

                        {configured ? (
                          <>
                            <div className="mdc-chat-agent-builder__provider-options">
                              <label>
                                <input
                                  type="checkbox"
                                  checked={configured.allowRead}
                                  onChange={(event) =>
                                    void updateAgentProviderPermissions(provider.providerKey, {
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
                                    void updateAgentProviderPermissions(provider.providerKey, {
                                      allowWrite: event.target.checked,
                                    })
                                  }
                                />
                                Escrita
                              </label>

                              <label>
                                <input
                                  type="checkbox"
                                  checked={configured.requiresConfirmationForWrite}
                                  onChange={(event) =>
                                    void updateAgentProviderPermissions(provider.providerKey, {
                                      requiresConfirmationForWrite: event.target.checked,
                                    })
                                  }
                                />
                                Confirmar escrita
                              </label>
                            </div>

                            <button
                              type="button"
                              className="mdc-chat-agent-builder__routes-toggle"
                              onClick={() =>
                                setSelectedProviderKey((current) =>
                                  current === provider.providerKey
                                    ? null
                                    : provider.providerKey,
                                )
                              }
                            >
                              {selectedProviderKey === provider.providerKey
                                ? "Ocultar rotas"
                                : `Ver rotas (${configured.actionCount})`}
                            </button>

                            {selectedProviderKey === provider.providerKey ? (
                              <div className="mdc-chat-agent-builder__route-list">
                                {isLoadingProviderActions ? (
                                  <p className="mdc-chat-muted">Carregando rotas...</p>
                                ) : null}

                                {!isLoadingProviderActions && providerActions.length === 0 ? (
                                  <p className="mdc-chat-muted">Nenhuma rota importada para esta API.</p>
                                ) : null}

                                {providerActions.map((action) => (
                                  <article key={action.actionId}>
                                    <label>
                                      <input
                                        type="checkbox"
                                        checked={isActionEnabledByOverride(action)}
                                        onChange={(event) =>
                                          void toggleProviderAction(
                                            action,
                                            event.target.checked,
                                          )
                                        }
                                      />

                                      <span>
                                        <strong>
                                          {action.method} {action.path}
                                        </strong>
                                        <small>
                                          {action.summary || action.operationId}
                                          {action.sensitivity
                                            ? ` · ${action.sensitivity}`
                                            : ""}
                                        </small>
                                      </span>
                                    </label>
                                  </article>
                                ))}
                              </div>
                            ) : null}
                          </>
                        ) : null}
                      </article>
                    );
                  })}

                  {availableProviders.length === 0 ? (
                    <p className="mdc-chat-muted">
                      Nenhuma API cadastrada. Cadastre uma API OpenAPI no painel administrativo.
                    </p>
                  ) : null}
                </div>
                </>
              ) : (
                <p className="mdc-chat-muted">Salve o agente antes de conectar APIs.</p>
              )}
            </section>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <div className="mdc-chat-agent-builder__section-title">
              <FileText size={18} aria-hidden="true" />
              <div>
                <h2>Fontes do agente</h2>
                <p>Arquivos e notas usados sempre que este agente estiver ativo.</p>
              </div>
            </div>

            {agent ? (
              <>
                <label className="mdc-chat-agent-builder__source-upload">
                  <Upload size={16} aria-hidden="true" />
                  <span>{isSavingSource ? "Enviando..." : "Enviar arquivo"}</span>
                  <input
                    type="file"
                    disabled={isSavingSource}
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      void uploadAgentKnowledgeFile(file);
                      event.target.value = "";
                    }}
                  />
                </label>

                <div className="mdc-chat-agent-builder__source-note">
                  <input
                    value={sourceTitle}
                    onChange={(event) => setSourceTitle(event.target.value)}
                    placeholder="Título da nota"
                  />
                  <textarea
                    value={sourceContent}
                    onChange={(event) => setSourceContent(event.target.value)}
                    rows={4}
                    placeholder="Cole contexto, políticas ou conhecimento do agente..."
                  />
                  <button
                    type="button"
                    disabled={isSavingSource || !sourceContent.trim()}
                    onClick={() => void createAgentKnowledgeNote()}
                  >
                    Adicionar nota
                  </button>
                </div>

                <div className="mdc-chat-agent-builder__source-list">
                  {agentSources.length > 0 ? (
                    agentSources.map((source) => (
                      <article key={source.id}>
                        <FileText size={16} aria-hidden="true" />
                        <span>
                          <strong>{source.title}</strong>
                          <small>
                            {source.original_filename || source.source_ref || source.source_type}
                            {typeof source.chunk_count === "number"
                              ? ` · ${source.chunk_count} trecho(s)`
                              : ""}
                          </small>
                        </span>
                        <button
                          type="button"
                          onClick={() => void removeAgentSource(source.id)}
                          title="Remover fonte"
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </article>
                    ))
                  ) : (
                    <p className="mdc-chat-muted">Nenhuma fonte adicionada.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="mdc-chat-muted">Salve o agente para adicionar fontes.</p>
            )}
          </section>

          {localError ? (
            <p className="mdc-chat-agent-builder__error">{localError}</p>
          ) : null}
        </form>

        <aside className="mdc-chat-agent-builder__preview">
          <div className="mdc-chat-agent-builder__preview-label">Pré-visualizar</div>

          <div className="mdc-chat-agent-builder__preview-card">
            <div className="mdc-chat-agent-builder__preview-avatar">
              <Bot size={26} aria-hidden="true" />
            </div>

            <h2>{name.trim() || "Novo agente"}</h2>

            <p>
              {description.trim() ||
                "Configure comportamento, instruções e quebra-gelos deste especialista."}
            </p>

            {normalizedIcebreakers.length > 0 ? (
              <div className="mdc-chat-agent-builder__preview-icebreakers">
                {normalizedIcebreakers.slice(0, 3).map((icebreaker) => (
                  <button key={icebreaker} type="button">
                    {icebreaker}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="mdc-chat-agent-builder__preview-input">
              Pergunte alguma coisa
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
