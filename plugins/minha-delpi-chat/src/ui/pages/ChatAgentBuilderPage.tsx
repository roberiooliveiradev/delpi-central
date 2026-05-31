import {
  ArrowLeft,
  Bot,
  Check,
  Copy,
  Download,
  Save,
  Upload,
  Plus,
  Send,
  Settings2,
  Sparkles,
  Trash2,
  Wand2,
  X,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useResizablePane } from "../../state/hooks/useResizablePane";
import { useConfirmDialog } from "../components/useConfirmDialog";

import {
  createAgentTextSource,
  deleteChatSource,
  downloadChatSource,
  duplicateChatAgent,
  exportChatAgent,
  getChatAgent,
  getChatAgentStats,
  importChatAgent,
  transferChatAgentOwnership,
  listAgentSources,
  listChatAgentActionProviders,
  listChatAgentSkills,
  listChatAgentShares,
  previewChatAgent,
  previewChatAgentDraft,
  publishChatAgent,
  listChatAgentVersions,
  revokeChatAgentShare,
  saveChatAgentActionProvider,
  deleteChatAgentActionProvider,
  shareChatAgent,
  uploadAgentSource,
} from "../../data/api/chatApi";
import { ChatUserSearchField } from "../components/ChatUserSearchField";
import type {
  ChatAgent,
  ChatAgentActionProvider,
  ChatAgentSkillBinding,
  ChatAgentExportBundle,
  ChatAgentShare,
  ChatAgentStats,
  ChatWorkspaceSource,
} from "../../data/api/chatTypes";

import { AGENT_CREATION_ASSISTANT_PROMPT } from "../../domain/agentCreationAssistant";
import {
  AGENT_SYSTEM_PROMPT_TEMPLATES,
  getAgentSystemPromptTemplate,
} from "../../domain/agentSystemPromptTemplates";
import { buildChatAgentHref } from "../../navigation/chatRoutes";
import { handleChatNavClick } from "../../navigation/chatNavigation";
import {
  AGENT_ICEBREAKER_MAX_CHARS,
  AGENT_ICEBREAKER_MAX_COUNT,
  clampIcebreakerDraft,
  formatIcebreakerForDisplay,
  getIcebreakerGridDensityClass,
  normalizeAgentIcebreakers,
} from "../agentIcebreakers";
import { DEFAULT_AGENT_ICEBREAKERS } from "../chatHomeStarters";

import { ChatAnimatedPanel } from "../components/ChatAnimatedPanel";
import { AgentBuilderCheckbox } from "../components/agent-builder/AgentBuilderCheckbox";
import { AgentBuilderSwitch } from "../components/agent-builder/AgentBuilderSwitch";
import { AgentKnowledgeSourcesPanel } from "../components/agent-builder/AgentKnowledgeSourcesPanel";
import { AgentMiniDashboard } from "../components/admin/agents/AgentMiniDashboard";
import "../components/admin/agents/AgentMiniDashboard.css";

import "../components/agent-builder/AgentKnowledgeSourcesPanel.css";
import "./ChatAgentBuilderPage.css";

type AgentPayload = {
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
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
};

type ChatAgentBuilderPageProps = {
  agent?: ChatAgent | null;
  onBack: () => void;
  onCreateAction?: (agent: ChatAgent) => void;
  onConfigureAction?: (agent: ChatAgent, providerKey: string) => void;
  onConfigureSkills?: (agent: ChatAgent) => void;
  onSelectAgent?: (agentId: string | null) => void;
  onCreateAgent?: (payload: AgentPayload) => Promise<ChatAgent | null>;
  onUpdateAgent?: (
    agentId: string,
    payload: AgentUpdatePayload,
  ) => Promise<ChatAgent | null>;
  onAgentPublished?: (agent: ChatAgent) => void;
  onAgentCreated?: (agent: ChatAgent) => void;
  onDeleteAgent?: (agentId: string) => Promise<boolean>;
  onDuplicateAgent?: (agent: ChatAgent) => void;
  canManageOfficialAgents?: boolean;
  onOpenRagAdmin?: (agentId: string) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function getAgentIcebreakers(agent?: ChatAgent | null): string[] {
  return normalizeAgentIcebreakers(agent?.metadata?.icebreakers);
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
  onCreateAction,
  onConfigureAction,
  onConfigureSkills,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onAgentPublished,
  onAgentCreated,
  onDeleteAgent,
  onDuplicateAgent,
  canManageOfficialAgents = false,
  onOpenRagAdmin,
  getAccessToken,
}: ChatAgentBuilderPageProps) {
  const isEditing = Boolean(agent);
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [builderMode, setBuilderMode] = useState<"create" | "configure">(
    agent ? "configure" : "create",
  );
  const [createBrief, setCreateBrief] = useState("");
  const [createInput, setCreateInput] = useState("");
  const [createMessages, setCreateMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([]);
  const [isCreateChatLoading, setIsCreateChatLoading] = useState(false);
  const [previewInput, setPreviewInput] = useState("");
  const [previewMessages, setPreviewMessages] = useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([]);

  const [name, setName] = useState(agent?.name ?? "");
  const [description, setDescription] = useState(agent?.description ?? "");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [selectedPromptTemplateKey, setSelectedPromptTemplateKey] = useState("");
  const [visibility, setVisibility] = useState(
    agent?.visibility === "system"
      ? "system"
      : agent?.visibility === "public"
        ? "public"
        : "private",
  );
  const [category, setCategory] = useState(agent?.category ?? "");
  const [icon, setIcon] = useState(agent?.icon ?? "bot");
  const [responseStyle, setResponseStyle] = useState(agent?.response_style ?? "objetivo");
  const [enabled, setEnabled] = useState(agent?.enabled ?? true);
  const [maxToolCalls, setMaxToolCalls] = useState(agent?.max_tool_calls ?? 5);
  const [requiresConfirmationForWrite, setRequiresConfirmationForWrite] = useState(
    agent?.requires_confirmation_for_write ?? false,
  );
  const [shareTargetUserId, setShareTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState<"viewer" | "editor">("viewer");
  const [isSharing, setIsSharing] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const [agentShares, setAgentShares] = useState<ChatAgentShare[]>([]);
  const [isLoadingShares, setIsLoadingShares] = useState(false);
  const [revokingShareUserId, setRevokingShareUserId] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isLoadingAgent, setIsLoadingAgent] = useState(false);
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

  const [agentActionProviders, setAgentActionProviders] = useState<ChatAgentActionProvider[]>([]);
  const [actionProviderBusyKey, setActionProviderBusyKey] = useState<string | null>(null);
  const [agentSkillBindings, setAgentSkillBindings] = useState<ChatAgentSkillBinding[]>([]);
  const [agentSources, setAgentSources] = useState<ChatWorkspaceSource[]>([]);
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceContent, setSourceContent] = useState("");
  const [isSavingSource, setIsSavingSource] = useState(false);
  const [sourceNotice, setSourceNotice] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDuplicating, setIsDuplicating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const importInputRef = useRef<HTMLInputElement>(null);
  const [copyActionsOnDuplicate, setCopyActionsOnDuplicate] = useState(true);
  const [copySourcesOnDuplicate, setCopySourcesOnDuplicate] = useState(false);
  const [transferTargetUserId, setTransferTargetUserId] = useState("");
  const [isTransferring, setIsTransferring] = useState(false);
  const [transferMessage, setTransferMessage] = useState<string | null>(null);
  const [updatingShareUserId, setUpdatingShareUserId] = useState<string | null>(null);
  const [agentLinkCopied, setAgentLinkCopied] = useState(false);
  const [agentStats, setAgentStats] = useState<ChatAgentStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [publishedVersion, setPublishedVersion] = useState(agent?.published_version ?? 0);
  const [hasUnpublishedChanges, setHasUnpublishedChanges] = useState(
    agent?.has_unpublished_changes ?? false,
  );
  const [isPublishing, setIsPublishing] = useState(false);
  const [agentVersions, setAgentVersions] = useState<
    { id: string; version: number; event: string; createdAt: string | null }[]
  >([]);


  useEffect(() => {
    let isMounted = true;

    async function loadAgentDetails() {
      if (!agent?.id || !getAccessToken) {
        setAgentSources([]);
        setAgentActionProviders([]);
        return;
      }

      setIsLoadingAgent(true);
      setLocalError(null);

      try {
        const [details, sources, actionProviders, skillBindings] = await Promise.all([
          getChatAgent(agent.id, { getAccessToken }),
          listAgentSources(agent.id, { getAccessToken }),
          listChatAgentActionProviders(agent.id, { getAccessToken }),
          listChatAgentSkills(agent.id, { getAccessToken }),
        ]);

        if (!isMounted) {
          return;
        }

        setName(details.name);
        setDescription(details.description ?? "");
        setSystemPrompt(details.system_prompt ?? "");
        setVisibility(
          details.visibility === "system"
            ? "system"
            : details.visibility === "public"
              ? "public"
              : "private",
        );
        setCategory(details.category ?? "");
        setIcon(details.icon ?? "bot");
        setResponseStyle(details.response_style ?? "objetivo");
        setEnabled(details.enabled);
        setMaxToolCalls(details.max_tool_calls);
        setRequiresConfirmationForWrite(details.requires_confirmation_for_write);
        setIcebreakers(
          getAgentIcebreakers(details).length > 0 ? getAgentIcebreakers(details) : [""],
        );

        const nextCapabilities = getMetadataRecord(details.metadata, "capabilities");
        setCapActions(
          typeof nextCapabilities.actions === "boolean" ? nextCapabilities.actions : true,
        );
        setCapFiles(
          typeof nextCapabilities.files === "boolean" ? nextCapabilities.files : true,
        );
        setCapCanvas(
          typeof nextCapabilities.canvas === "boolean" ? nextCapabilities.canvas : true,
        );

        setAgentSources(sources);
        setAgentActionProviders(actionProviders);
        setAgentSkillBindings(skillBindings);
        setPublishedVersion(details.published_version ?? 0);
        setHasUnpublishedChanges(details.has_unpublished_changes ?? false);
      } catch {
        if (isMounted) {
          setLocalError("Não foi possível carregar os detalhes completos do agente.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingAgent(false);
        }
      }
    }

    void loadAgentDetails();

    return () => {
      isMounted = false;
    };
  }, [agent?.id, getAccessToken]);

  async function reloadAgentActionProviders() {
    if (!agent?.id || !getAccessToken) {
      setAgentActionProviders([]);
      return;
    }

    const actionProviders = await listChatAgentActionProviders(agent.id, { getAccessToken });
    setAgentActionProviders(actionProviders);
  }

  async function toggleAgentActionProvider(
    provider: ChatAgentActionProvider,
    enabled: boolean,
  ) {
    if (!agent?.id) {
      return;
    }

    setActionProviderBusyKey(provider.providerKey);
    setLocalError(null);

    try {
      await saveChatAgentActionProvider(
        agent.id,
        {
          providerKey: provider.providerKey,
          enabled,
          allowRead: provider.allowRead,
          allowWrite: provider.allowWrite,
          allowAdmin: provider.allowAdmin,
          requiresConfirmationForWrite: provider.requiresConfirmationForWrite,
        },
        { getAccessToken },
      );
      await reloadAgentActionProviders();
    } catch (error) {
      setLocalError(
        error instanceof Error
          ? error.message
          : `Não foi possível ${enabled ? "ativar" : "desativar"} a action.`,
      );
    } finally {
      setActionProviderBusyKey(null);
    }
  }

  async function removeAgentActionProvider(provider: ChatAgentActionProvider) {
    if (!agent?.id) {
      return;
    }

    const confirmed = await confirm({
      title: "Excluir action do agente",
      description: `Remover "${provider.providerName || provider.providerKey}" deste agente? O provider global permanece cadastrado.`,
      confirmLabel: "Excluir",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setActionProviderBusyKey(provider.providerKey);
    setLocalError(null);

    try {
      await deleteChatAgentActionProvider(agent.id, provider.providerKey, {
        getAccessToken,
      });
      await reloadAgentActionProviders();
    } catch (error) {
      setLocalError(
        error instanceof Error
          ? error.message
          : "Não foi possível excluir a action.",
      );
    } finally {
      setActionProviderBusyKey(null);
    }
  }



  async function uploadAgentKnowledgeFiles(files: File[]) {
    if (!agent || files.length === 0) {
      return;
    }

    setIsSavingSource(true);
    setSourceNotice(null);

    const duplicateNames: string[] = [];
    let uploadedCount = 0;
    try {
      for (const file of files) {
        const result = await uploadAgentSource(agent.id, file, { getAccessToken });

        if (result.duplicate) {
          duplicateNames.push(result.original_filename || result.title || file.name);
          continue;
        }

        uploadedCount += 1;
      }

      setAgentSources(await listAgentSources(agent.id, { getAccessToken }));

      if (duplicateNames.length > 0 && uploadedCount === 0) {
        setSourceNotice(
          duplicateNames.length === 1
            ? `"${duplicateNames[0]}" já está neste agente (mesmo conteúdo).`
            : `${duplicateNames.length} arquivo(s) ignorado(s): conteúdo já existente.`,
        );
      } else if (duplicateNames.length > 0) {
        setSourceNotice(
          `${uploadedCount} arquivo(s) adicionado(s). ${duplicateNames.length} duplicado(s) ignorado(s).`,
        );
      }
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
      const result = await createAgentTextSource(
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

      if (result.duplicate) {
        setSourceNotice("Esta nota tem o mesmo conteúdo de uma fonte já vinculada ao agente.");
      } else {
        setSourceNotice(null);
        setSourceTitle("");
        setSourceContent("");
      }

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

  async function downloadAgentSource(sourceId: string) {
    await downloadChatSource(sourceId, { getAccessToken });
  }

  const normalizedIcebreakers = useMemo(
    () =>
      icebreakers
        .map((item) => clampIcebreakerDraft(item.trim()))
        .filter(Boolean)
        .slice(0, AGENT_ICEBREAKER_MAX_COUNT),
    [icebreakers],
  );

  const previewIcebreakers = useMemo(
    () =>
      normalizedIcebreakers.length > 0 ? normalizedIcebreakers : DEFAULT_AGENT_ICEBREAKERS,
    [normalizedIcebreakers],
  );

  const usingDefaultPreviewIcebreakers = normalizedIcebreakers.length === 0;
  const previewIcebreakerDensityClass = getIcebreakerGridDensityClass(
    Math.min(previewIcebreakers.length, 3),
  );

  function updateIcebreaker(index: number, value: string) {
    const nextValue = clampIcebreakerDraft(value);

    setIcebreakers((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? nextValue : item)),
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
      if (current.length >= AGENT_ICEBREAKER_MAX_COUNT) {
        return current;
      }

      return [...current, ""];
    });
  }

  useEffect(() => {
    if (agent?.id) {
      setBuilderMode("configure");
    }
  }, [agent?.id]);

  const icebreakersSection = (
    <section
      id="agent-icebreakers"
      className="mdc-chat-agent-builder__section mdc-chat-agent-builder__icebreakers-section"
      aria-label="Quebra-gelos do agente"
    >
      <h2 className="mdc-chat-ws-section-head">Quebra-gelos</h2>
      <p className="mdc-chat-agent-builder__icebreakers-help">
        Até {AGENT_ICEBREAKER_MAX_COUNT} sugestões na página do agente, com no máximo{" "}
        {AGENT_ICEBREAKER_MAX_CHARS} caracteres cada. Cards menores quando houver mais sugestões.
      </p>

      <div className="mdc-chat-agent-builder__icebreakers">
        {icebreakers.map((icebreaker, index) => (
          <div key={`${index}-${icebreakers.length}`} className="mdc-chat-agent-builder__icebreaker-row">
            <input
              value={icebreaker}
              maxLength={AGENT_ICEBREAKER_MAX_CHARS}
              onChange={(event) => updateIcebreaker(index, event.target.value)}
              placeholder="Ex.: Quero verificar um desenho."
              aria-label={`Quebra-gelo ${index + 1}`}
              aria-describedby={`icebreaker-count-${index}`}
            />
            <span
              id={`icebreaker-count-${index}`}
              className="mdc-chat-agent-builder__icebreaker-count"
            >
              {icebreaker.length}/{AGENT_ICEBREAKER_MAX_CHARS}
            </span>

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
          className="mdc-chat-ws-outline-btn"
          onClick={addIcebreaker}
          disabled={icebreakers.length >= AGENT_ICEBREAKER_MAX_COUNT}
        >
          <Plus size={16} aria-hidden="true" />
          <span>Adicionar quebra-gelo</span>
        </button>
      </div>
    </section>
  );

  const activeBuilderMode = isEditing ? "configure" : builderMode;
  const showConfigureForm = isEditing || builderMode === "configure";

  function applyDraftFromBrief(brief: string, options?: { switchToConfigure?: boolean }) {
    const normalizedBrief = brief.trim();

    if (!normalizedBrief) {
      return false;
    }

    const firstSentence =
      normalizedBrief.split(/[.!?\n]/).find(Boolean)?.trim() || normalizedBrief;
    const generatedName =
      name.trim() ||
      firstSentence
        .replace(/^crie\s+(um|uma)?\s*/i, "")
        .replace(/^agente\s+(para|de)?\s*/i, "")
        .slice(0, 80);

    const finalName = generatedName || "Novo agente";

    setName(finalName);
    setDescription((current) => current.trim() || firstSentence.slice(0, 240));
    setSystemPrompt((current) => {
      if (current.trim()) {
        return current;
      }

      return [
        `Você é ${finalName}, um agente especializado da Minha DELPI.`,
        "",
        "Objetivo:",
        normalizedBrief,
        "",
        "Regras:",
        "- Responda com clareza e objetividade.",
        "- Use fontes, arquivos e actions autorizadas quando estiverem configuradas.",
        "- Não invente dados operacionais; quando precisar, consulte as ferramentas disponíveis.",
        "- Explique limitações quando uma informação não estiver disponível.",
      ].join("\n");
    });

    setIcebreakers((current) => {
      const filled = current.map((item) => item.trim()).filter(Boolean);

      if (filled.length > 0) {
        return current;
      }

      return [
        "O que você consegue fazer?",
        "Quais informações você pode consultar?",
        "Me ajude com uma análise inicial.",
      ];
    });

    if (options?.switchToConfigure !== false) {
      setBuilderMode("configure");
    }

    setLocalError(null);
    return true;
  }

  function generateDraftFromBrief() {
    const brief = createBrief.trim() || createInput.trim();

    if (!brief && createMessages.length === 0) {
      setLocalError("Descreva o agente que deseja criar.");
      return;
    }

    const combinedBrief =
      brief ||
      createMessages
        .filter((message) => message.role === "user")
        .map((message) => message.content)
        .join("\n\n");

    setCreateBrief(combinedBrief);
    applyDraftFromBrief(combinedBrief, { switchToConfigure: true });
  }

  async function sendCreateChatMessage(content?: string) {
    const message = (content ?? createInput).trim();

    if (!message || !getAccessToken) {
      return;
    }

    const nextMessages: Array<{ role: "user" | "assistant"; content: string }> = [
      ...createMessages,
      { role: "user", content: message },
    ];

    setCreateMessages(nextMessages);
    setCreateInput("");
    setIsCreateChatLoading(true);
    setLocalError(null);

    const combinedBrief = nextMessages
      .filter((entry) => entry.role === "user")
      .map((entry) => entry.content)
      .join("\n\n");

    setCreateBrief(combinedBrief);
    applyDraftFromBrief(combinedBrief, { switchToConfigure: false });

    try {
      const result = await previewChatAgentDraft(
        {
          message,
          generateAnswer: true,
          draft: {
            name: "Assistente de criação",
            description: "Ajuda a definir novos agentes corporativos",
            systemPrompt: AGENT_CREATION_ASSISTANT_PROMPT,
            metadata: { icebreakers: [] },
          },
        },
        { getAccessToken },
      );

      const answer =
        (typeof result.answerPreview === "string" && result.answerPreview) ||
        (typeof result.answer === "string" && result.answer) ||
        "Não consegui responder agora. Tente reformular o pedido.";

      setCreateMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch {
      setCreateMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "Não foi possível continuar a conversa. Verifique sua conexão e tente novamente.",
        },
      ]);
    } finally {
      setIsCreateChatLoading(false);
    }
  }

  function buildPreviewDraft() {
    const normalizedName = name.trim();
    const existingPersonality =
      (agent?.metadata?.personality as Record<string, unknown> | undefined) ?? {};

    return {
      name: normalizedName || "Novo agente",
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      responseStyle,
      category: category.trim() || null,
      icon: icon.trim() || null,
      maxToolCalls,
      requiresConfirmationForWrite,
      metadata: {
        ...(agent?.metadata ?? {}),
        icebreakers: normalizedIcebreakers,
        personality: {
          tone:
            (existingPersonality.tone as string | undefined) ??
            "amigável e bem-humorado com moderação",
          humorLevel: (existingPersonality.humorLevel as number | undefined) ?? 2,
          emojiLevel: (existingPersonality.emojiLevel as number | undefined) ?? 0,
          proactivity: (existingPersonality.proactivity as boolean | undefined) ?? true,
          suggestFollowUps:
            (existingPersonality.suggestFollowUps as boolean | undefined) ?? true,
        },
        allowed_actions: allowedActions,
        capabilities: {
          ...capabilities,
          actions: capActions,
          files: capFiles,
          canvas: capCanvas,
        },
      },
    };
  }

  async function sendPreviewMessage(content?: string) {
    const message = (content ?? previewInput).trim();

    if (!message) {
      return;
    }

    if (!getAccessToken) {
      return;
    }

    const draft = buildPreviewDraft();

    if (!draft.name.trim()) {
      setPreviewMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "Informe o nome do agente para testar a pré-visualização.",
        },
      ]);
      return;
    }

    setPreviewMessages((current) => [...current, { role: "user", content: message }]);
    setPreviewInput("");
    setIsPreviewLoading(true);

    try {
      const result = agent?.id
        ? await previewChatAgent(
            agent.id,
            { message, generateAnswer: true, draft },
            { getAccessToken },
          )
        : await previewChatAgentDraft(
            { message, generateAnswer: true, draft },
            { getAccessToken },
          );

      const answer =
        (typeof result.answerPreview === "string" && result.answerPreview) ||
        (typeof result.answer === "string" && result.answer) ||
        "Sem resposta na pré-visualização.";

      setPreviewMessages((current) => [...current, { role: "assistant", content: answer }]);
    } catch {
      setPreviewMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "Não foi possível gerar a pré-visualização com o rascunho atual.",
        },
      ]);
    } finally {
      setIsPreviewLoading(false);
    }
  }

  const loadAgentShares = useCallback(async () => {
    if (!agent?.id || agent.access_role !== "owner" || !getAccessToken) {
      setAgentShares([]);
      return;
    }

    setIsLoadingShares(true);

    try {
      const shares = await listChatAgentShares(agent.id, { getAccessToken });
      setAgentShares(shares);
    } catch {
      setAgentShares([]);
    } finally {
      setIsLoadingShares(false);
    }
  }, [agent?.access_role, agent?.id, getAccessToken]);

  useEffect(() => {
    void loadAgentShares();
  }, [loadAgentShares]);

  useEffect(() => {
    async function loadVersions() {
      if (!agent?.id || !getAccessToken) {
        setAgentVersions([]);
        return;
      }

      try {
        const versions = await listChatAgentVersions(agent.id, { getAccessToken });
        setAgentVersions(versions);
      } catch {
        setAgentVersions([]);
      }
    }

    void loadVersions();
  }, [agent?.id, getAccessToken, publishedVersion]);

  useEffect(() => {
    let isMounted = true;

    async function loadStats() {
      if (!agent?.id || !getAccessToken) {
        setAgentStats(null);
        return;
      }

      if (!["owner", "editor", "system"].includes(agent.access_role)) {
        setAgentStats(null);
        return;
      }

      setIsLoadingStats(true);

      try {
        const stats = await getChatAgentStats(agent.id, { getAccessToken, hours: 168 });

        if (isMounted) {
          setAgentStats(stats);
        }
      } catch {
        if (isMounted) {
          setAgentStats(null);
        }
      } finally {
        if (isMounted) {
          setIsLoadingStats(false);
        }
      }
    }

    void loadStats();

    return () => {
      isMounted = false;
    };
  }, [agent?.access_role, agent?.id, getAccessToken]);

  async function revokeAgentShare(targetUserId: string) {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setRevokingShareUserId(targetUserId);

    try {
      await revokeChatAgentShare(agent.id, targetUserId, { getAccessToken });
      setShareMessage("Acesso revogado.");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível revogar o acesso.");
    } finally {
      setRevokingShareUserId(null);
    }
  }

  function buildSavePayload(): AgentPayload | null {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do agente.");
      return null;
    }

    const existingPersonality =
      (agent?.metadata?.personality as Record<string, unknown> | undefined) ?? {};

    return {
      name: normalizedName,
      description: description.trim() || null,
      systemPrompt: systemPrompt.trim() || null,
      visibility,
      category: category.trim() || null,
      icon: icon.trim() || null,
      responseStyle,
      metadata: {
        ...(agent?.metadata ?? {}),
        icebreakers: normalizedIcebreakers,
        personality: {
          tone:
            (existingPersonality.tone as string | undefined) ??
            "amigável e bem-humorado com moderação",
          humorLevel: (existingPersonality.humorLevel as number | undefined) ?? 2,
          emojiLevel: (existingPersonality.emojiLevel as number | undefined) ?? 0,
          proactivity: (existingPersonality.proactivity as boolean | undefined) ?? true,
          suggestFollowUps:
            (existingPersonality.suggestFollowUps as boolean | undefined) ?? true,
        },
        allowed_actions: allowedActions,
        capabilities: {
          ...capabilities,
          actions: capActions,
          files: capFiles,
          canvas: capCanvas,
        },
      },
    };
  }

  async function saveDraft(options?: { exitAfterSave?: boolean }) {
    const payload = buildSavePayload();

    if (!payload) {
      return null;
    }

    setIsSaving(true);
    setLocalError(null);

    try {
      if (agent) {
        const updated = await onUpdateAgent?.(agent.id, {
          ...payload,
          enabled,
          maxToolCalls,
          requiresConfirmationForWrite,
        });

        if (updated) {
          setPublishedVersion(updated.published_version ?? publishedVersion);
          setHasUnpublishedChanges(updated.has_unpublished_changes ?? true);
          onSelectAgent?.(updated.id);

          if (options?.exitAfterSave) {
            onBack();
          }
        }

        return updated ?? null;
      }

      const created = await onCreateAgent?.(payload);

      if (created) {
        setPublishedVersion(created.published_version ?? 0);
        setHasUnpublishedChanges(created.has_unpublished_changes ?? true);
        onSelectAgent?.(created.id);
        onAgentCreated?.(created);

        if (options?.exitAfterSave) {
          onBack();
        }
      }

      return created ?? null;
    } finally {
      setIsSaving(false);
    }
  }

  async function publishAgent() {
    const saved = await saveDraft();

    if (!saved?.id || !getAccessToken) {
      setLocalError("Salve o agente antes de publicar.");
      return;
    }

    setIsPublishing(true);
    setLocalError(null);

    try {
      const published = await publishChatAgent(saved.id, { getAccessToken });
      setPublishedVersion(published.published_version ?? 0);
      setHasUnpublishedChanges(published.has_unpublished_changes ?? false);
      onAgentPublished?.(published);
      onSelectAgent?.(published.id);
    } catch (error) {
      const message =
        error instanceof Error && error.message.trim()
          ? error.message.trim()
          : "Não foi possível publicar o agente.";
      setLocalError(message);
    } finally {
      setIsPublishing(false);
    }
  }

  async function submitForm() {
    await saveDraft({ exitAfterSave: true });
  }

  async function updateAgentShareRole(targetUserId: string, role: "viewer" | "editor") {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setUpdatingShareUserId(targetUserId);
    setShareMessage(null);

    try {
      await shareChatAgent(
        agent.id,
        { targetUserId, role },
        { getAccessToken },
      );
      setShareMessage("Papel atualizado.");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível atualizar o papel.");
    } finally {
      setUpdatingShareUserId(null);
    }
  }

  async function transferAgentOwnership() {
    if (!agent?.id || !getAccessToken || agent.access_role !== "owner") {
      return;
    }

    const newOwnerUserId = transferTargetUserId.trim();

    if (!newOwnerUserId) {
      setTransferMessage("Selecione o novo proprietário.");
      return;
    }

    const confirmed = await confirm({
      title: "Transferir propriedade",
      description:
        "Transferir a propriedade deste agente? Você perderá o papel de dono.",
      confirmLabel: "Transferir",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setIsTransferring(true);
    setTransferMessage(null);

    try {
      await transferChatAgentOwnership(agent.id, newOwnerUserId, { getAccessToken });
      setTransferMessage("Propriedade transferida. Saindo do builder...");
      setTransferTargetUserId("");
      onBack();
    } catch {
      setTransferMessage("Não foi possível transferir a propriedade.");
    } finally {
      setIsTransferring(false);
    }
  }

  async function shareCurrentAgent() {
    if (!agent || agent.access_role !== "owner") {
      return;
    }

    const targetUserId = shareTargetUserId.trim();

    if (!targetUserId) {
      setShareMessage("Selecione um usuário para compartilhar.");
      return;
    }

    setIsSharing(true);
    setShareMessage(null);

    try {
      await shareChatAgent(
        agent.id,
        { targetUserId, role: shareRole },
        { getAccessToken },
      );
      setShareMessage("Agente compartilhado com sucesso.");
      setShareTargetUserId("");
      await loadAgentShares();
    } catch {
      setShareMessage("Não foi possível compartilhar o agente.");
    } finally {
      setIsSharing(false);
    }
  }

  async function exportCurrentAgent() {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setIsExporting(true);
    setLocalError(null);

    try {
      const bundle = await exportChatAgent(agent.id, { getAccessToken });
      const blob = new Blob([JSON.stringify(bundle, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${agent.name || "agente"}-export.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setLocalError("Não foi possível exportar o agente.");
    } finally {
      setIsExporting(false);
    }
  }

  async function importAgentFromFile(file: File) {
    if (!getAccessToken) {
      return;
    }

    setIsImporting(true);
    setLocalError(null);

    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as { export?: unknown } | Record<string, unknown>;
      const exportPayload =
        parsed && typeof parsed === "object" && "export" in parsed
          ? (parsed.export as Record<string, unknown>)
          : parsed;

      const imported = await importChatAgent(
        {
          export: exportPayload as ChatAgentExportBundle,
          applyActions: true,
        },
        { getAccessToken },
      );

      onDuplicateAgent?.(imported);
    } catch {
      setLocalError("Não foi possível importar o arquivo. Verifique o JSON exportado.");
    } finally {
      setIsImporting(false);
    }
  }

  async function duplicateCurrentAgent() {
    if (!agent?.id || !getAccessToken) {
      return;
    }

    setIsDuplicating(true);
    setLocalError(null);

    try {
      const duplicated = await duplicateChatAgent(agent.id, {
        getAccessToken,
        copyActions: copyActionsOnDuplicate,
        copySources: copySourcesOnDuplicate,
      });
      onDuplicateAgent?.(duplicated);
    } catch {
      setLocalError("Não foi possível duplicar o agente.");
    } finally {
      setIsDuplicating(false);
    }
  }

  async function deleteCurrentAgent() {
    if (!agent) {
      return;
    }

    const confirmed = await confirm({
      title: "Excluir agente",
      description: `Excluir o agente "${agent.name}"?`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    const deleted = await onDeleteAgent?.(agent.id);

    if (deleted) {
      onSelectAgent?.(null);
      onBack();
    }
  }

  const canExportAgent =
    agent && ["owner", "editor", "system"].includes(agent.access_role);
  const canImportAgent = Boolean(onCreateAgent);
  const agentUsagePath = useMemo(() => {
    if (!agent?.id) {
      return null;
    }

    return buildChatAgentHref(agent.id);
  }, [agent?.id]);
  const agentUsageUrl = useMemo(() => {
    if (!agentUsagePath) {
      return null;
    }

    if (typeof window === "undefined") {
      return agentUsagePath;
    }

    return `${window.location.origin}${agentUsagePath}`;
  }, [agentUsagePath]);

  async function copyAgentUsageLink() {
    if (!agentUsageUrl) {
      return;
    }

    try {
      await navigator.clipboard.writeText(agentUsageUrl);
      setAgentLinkCopied(true);
      window.setTimeout(() => setAgentLinkCopied(false), 1800);
    } catch {
      setLocalError("Não foi possível copiar o link do agente.");
    }
  }

  const {
    layoutRef,
    layoutStyle,
    splitEnabled,
    isDragging,
    onSplitterPointerDown,
  } = useResizablePane({
    storageKey: "minha-delpi-chat.agent-builder.preview-width",
    defaultWidth: 380,
    minWidth: 260,
    maxWidthRatio: 0.48,
    minSplitWidth: 900,
  });

  const layoutClassName = [
    "mdc-chat-agent-builder__layout",
    splitEnabled ? "mdc-chat-agent-builder__layout--split" : "",
    isDragging ? "mdc-chat-agent-builder__layout--dragging" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className="mdc-chat-agent-builder" aria-label="Configurar agente">
      {confirmDialog}
      <header className="mdc-chat-ws-topbar mdc-chat-agent-builder__topbar">
        <div className="mdc-chat-ws-topbar__start">
          <button type="button" className="mdc-chat-ws-topbar__back" onClick={onBack}>
            <ArrowLeft size={18} aria-hidden="true" />
            <span>Voltar para agentes</span>
          </button>
        </div>

        <div className="mdc-chat-ws-topbar__title mdc-chat-agent-builder__topbar-title">
          <span>{name.trim() || (isEditing ? "Configurar agente" : "Criar agente")}</span>
          {isEditing ? (
            <small className="mdc-chat-agent-builder__topbar-meta">
              {publishedVersion > 0 ? (
                <em className="mdc-chat-agent-builder__live-badge">
                  Publicado v{publishedVersion}
                </em>
              ) : (
                <em className="mdc-chat-agent-builder__live-badge mdc-chat-agent-builder__live-badge--off">
                  Não publicado
                </em>
              )}
              {hasUnpublishedChanges ? <span>· Alterações não publicadas</span> : null}
              {!enabled ? <span>· Inativo</span> : null}
            </small>
          ) : (
            <small>Rascunho — salve para testar com fontes e publicar</small>
          )}
        </div>

        <div className="mdc-chat-ws-topbar__actions mdc-chat-agent-builder__topbar-actions">
          {canImportAgent ? (
            <>
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn"
                disabled={isImporting}
                title="Importar configuração em JSON"
                onClick={() => importInputRef.current?.click()}
              >
                <Upload size={16} aria-hidden="true" />
                <span>{isImporting ? "Importando..." : "Importar JSON"}</span>
              </button>
              <input
                ref={importInputRef}
                type="file"
                className="mdc-chat-agent-builder__sr-only"
                accept="application/json,.json"
                disabled={isImporting}
                onChange={(event) => {
                  const file = event.target.files?.[0];

                  if (file) {
                    void importAgentFromFile(file);
                  }

                  event.target.value = "";
                }}
              />
            </>
          ) : null}

          {canExportAgent ? (
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn"
              disabled={isExporting}
              onClick={() => void exportCurrentAgent()}
              title="Baixa configuração em JSON"
            >
              <Download size={16} aria-hidden="true" />
              <span>{isExporting ? "Exportando..." : "Exportar"}</span>
            </button>
          ) : null}

          {agent ? (
            <>
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn"
                disabled={isDuplicating}
                onClick={() => void duplicateCurrentAgent()}
                title="Cria cópia privada do agente"
              >
                <Copy size={16} aria-hidden="true" />
                <span>{isDuplicating ? "Duplicando..." : "Duplicar"}</span>
              </button>
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--danger"
                onClick={() => void deleteCurrentAgent()}
                title="Excluir agente"
              >
                <Trash2 size={17} aria-hidden="true" />
                <span>Excluir</span>
              </button>
            </>
          ) : null}

          <button
            type="button"
            className="mdc-chat-ws-toolbar-btn"
            disabled={isSaving || isPublishing}
            onClick={() => void saveDraft()}
            title="Salvar alterações como rascunho"
          >
            <Save size={16} aria-hidden="true" />
            <span>{isSaving ? "Salvando..." : "Salvar rascunho"}</span>
          </button>

          {agent?.id ? (
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              disabled={isSaving || isPublishing}
              onClick={() => void publishAgent()}
              title="Publicar versão para usuários"
            >
              <Check size={17} aria-hidden="true" />
              <span>{isPublishing ? "Publicando..." : "Publicar"}</span>
            </button>
          ) : (
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              disabled={isSaving}
              onClick={() => void saveDraft()}
              title="Criar agente e salvar rascunho"
            >
              <Check size={17} aria-hidden="true" />
              <span>{isSaving ? "Salvando..." : "Criar e salvar"}</span>
            </button>
          )}
        </div>
      </header>

      <div ref={layoutRef} className={layoutClassName} style={layoutStyle}>
        <form
          className="mdc-chat-agent-builder__form"
          onSubmit={(event) => {
            event.preventDefault();
            void submitForm();
          }}
        >
          <div className="mdc-chat-agent-builder__panel">
          {!isEditing ? (
            <div className="mdc-chat-agent-builder__switch" role="tablist" aria-label="Modo de edição">
              <button
                type="button"
                className={activeBuilderMode === "create" ? "is-active" : ""}
                onClick={() => setBuilderMode("create")}
              >
                Criar
              </button>
              <button
                type="button"
                className={activeBuilderMode === "configure" ? "is-active" : ""}
                onClick={() => setBuilderMode("configure")}
              >
                Configurar
              </button>
            </div>
          ) : null}

          <ChatAnimatedPanel panelKey={showConfigureForm ? "configure" : "create"} variant="tab">
          {!showConfigureForm ? (
            <section className="mdc-chat-agent-builder__section mdc-chat-agent-builder__create-mode">
              <h2 className="mdc-chat-ws-section-head">Criar conversando</h2>
              <p className="mdc-chat-ws-section-lead">
                Descreva o especialista em linguagem natural. O assistente ajuda a montar o
                rascunho; a pré-visualização à direita usa as mesmas configurações em tempo real.
              </p>

              <div className="mdc-chat-ws-create-chat">
                <div className="mdc-chat-ws-create-chat__messages">
                  {createMessages.length === 0 ? (
                    <p className="mdc-chat-ws-empty">
                      Ex.: &quot;Preciso de um agente para suporte de produtos DELPI, que consulte
                      estoque via API e responda de forma objetiva.&quot;
                    </p>
                  ) : (
                    createMessages.map((message, index) => (
                      <div
                        key={`${message.role}-${index}`}
                        className={
                          message.role === "user"
                            ? "mdc-chat-ws-create-chat__bubble mdc-chat-ws-create-chat__bubble--user"
                            : "mdc-chat-ws-create-chat__bubble mdc-chat-ws-create-chat__bubble--assistant"
                        }
                      >
                        {message.content}
                      </div>
                    ))
                  )}
                  {isCreateChatLoading ? (
                    <div className="mdc-chat-ws-create-chat__bubble mdc-chat-ws-create-chat__bubble--assistant">
                      Pensando...
                    </div>
                  ) : null}
                </div>

                <div className="mdc-chat-ws-create-chat__composer">
                  <textarea
                    value={createInput}
                    rows={2}
                    disabled={isCreateChatLoading}
                    onChange={(event) => setCreateInput(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        void sendCreateChatMessage();
                      }
                    }}
                    placeholder="Descreva o agente ou responda às perguntas..."
                  />
                  <button
                    type="button"
                    disabled={isCreateChatLoading || !createInput.trim()}
                    aria-label="Enviar mensagem"
                    onClick={() => void sendCreateChatMessage()}
                  >
                    <Send size={16} aria-hidden="true" />
                  </button>
                </div>
              </div>

              <div className="mdc-chat-agent-builder__create-actions">
                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  disabled={isCreateChatLoading}
                  onClick={() => void sendCreateChatMessage()}
                >
                  <Send size={16} aria-hidden="true" />
                  <span>Enviar</span>
                </button>

                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  disabled={isCreateChatLoading}
                  onClick={generateDraftFromBrief}
                >
                  <Wand2 size={16} aria-hidden="true" />
                  <span>Aplicar rascunho e revisar</span>
                </button>
              </div>

              <div className="mdc-chat-agent-builder__placeholder">
                <strong>Próximo passo</strong>
                <p>
                  Use &quot;Aplicar rascunho e revisar&quot; para abrir a aba Configurar com nome,
                  instruções e quebra-gelos preenchidos.
                </p>
              </div>
            </section>
          ) : (
            <>
          <header className="mdc-chat-agent-builder__hero">
            <span className="mdc-chat-agent-builder__hero-icon" aria-hidden="true">
              <Bot size={26} />
            </span>
            <label className="mdc-chat-agent-builder__hero-name-wrap">
              <span className="mdc-chat-agent-builder__sr-only">Nome do agente</span>
              <input
                className="mdc-chat-agent-builder__hero-name"
                value={name}
                maxLength={120}
                onChange={(event) => {
                  setName(event.target.value);
                }}
                placeholder="Nome do agente"
              />
            </label>
          </header>

          <section className="mdc-chat-agent-builder__section mdc-chat-agent-builder__section--flat">
            <label className="mdc-chat-ws-field">
              <span>Descrição</span>
              <textarea
                value={description}
                rows={2}
                maxLength={900}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique quando este agente deve ser usado..."
              />
            </label>
          </section>

          {icebreakersSection}

          <section
            className="mdc-chat-agent-builder__section mdc-chat-agent-builder__identity-section"
            aria-label="Visibilidade do agente"
          >
            <h2 className="mdc-chat-ws-section-head">Visibilidade</h2>

            <div className="mdc-chat-agent-builder__grid">
              <label className="mdc-chat-ws-field">
                <span>Visibilidade</span>
                <select
                  value={visibility}
                  onChange={(event) => setVisibility(event.target.value)}
                >
                  <option value="private">Privado</option>
                  <option value="public">Público interno</option>
                  {canManageOfficialAgents ? (
                    <option value="system">Oficial</option>
                  ) : null}
                </select>
                <small>
                  Privado: só quem tem acesso. Público interno: visível na lista para a
                  empresa. Oficial: agente corporativo padrão (requer permissão).
                </small>
              </label>
            </div>

            {isEditing && agentUsagePath ? (
              <div className="mdc-chat-agent-builder__agent-link">
                <span className="mdc-chat-agent-builder__agent-link-label">Link de uso</span>
                <div className="mdc-chat-agent-builder__agent-link-row">
                  <a
                    href={agentUsagePath}
                    onClick={(event) => handleChatNavClick(event, agentUsagePath)}
                  >
                    {agentUsageUrl}
                  </a>
                  <button
                    type="button"
                    className="mdc-chat-ws-outline-btn"
                    onClick={() => void copyAgentUsageLink()}
                    title="Copiar link do agente"
                  >
                    <Copy size={15} aria-hidden="true" />
                    <span>{agentLinkCopied ? "Copiado" : "Copiar"}</span>
                  </button>
                </div>
                <small>Mesma URL usada ao abrir o agente no chat.</small>
              </div>
            ) : null}

            <div className="mdc-chat-agent-builder__grid mdc-chat-agent-builder__grid--three">
              <label className="mdc-chat-ws-field">
                <span>Categoria</span>
                <input
                  value={category}
                  maxLength={80}
                  onChange={(event) => setCategory(event.target.value)}
                  placeholder="Produtos"
                />
              </label>

              <label className="mdc-chat-ws-field">
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
            <h2 className="mdc-chat-ws-section-head">Instruções</h2>

            <div className="mdc-chat-agent-builder__prompt-templates">
              <label className="mdc-chat-ws-field">
                <span>Modelo de instruções</span>
                <select
                  value={selectedPromptTemplateKey}
                  onChange={async (event) => {
                    const templateKey = event.target.value;
                    setSelectedPromptTemplateKey(templateKey);

                    if (!templateKey) {
                      return;
                    }

                    const template = getAgentSystemPromptTemplate(templateKey);

                    if (!template) {
                      return;
                    }

                    const shouldReplace =
                      !systemPrompt.trim() ||
                      (await confirm({
                        title: "Substituir instruções",
                        description:
                          "Substituir as instruções atuais pelo modelo selecionado?",
                        confirmLabel: "Substituir",
                        cancelLabel: "Cancelar",
                        danger: true,
                      }));

                    if (!shouldReplace) {
                      return;
                    }

                    setSystemPrompt(template.prompt);
                    setResponseStyle(template.suggestedResponseStyle);
                  }}
                >
                  <option value="">Selecione um modelo (opcional)</option>
                  {AGENT_SYSTEM_PROMPT_TEMPLATES.map((template) => (
                    <option key={template.key} value={template.key}>
                      {template.label}
                    </option>
                  ))}
                </select>
                <small>
                  {selectedPromptTemplateKey
                    ? getAgentSystemPromptTemplate(selectedPromptTemplateKey)
                        ?.description
                    : "Modelos prontos para agentes operacionais, documentais ou híbridos (Onda 7)."}
                </small>
              </label>
            </div>

            <label className="mdc-chat-ws-field">
              <span>Instruções do agente</span>
              <textarea
                className="mdc-chat-agent-builder__prompt"
                value={systemPrompt}
                maxLength={12000}
                onChange={(event) => setSystemPrompt(event.target.value)}
                placeholder="Defina comportamento, tom, limites, regras e ações permitidas..."
              />
              <small>
                {isLoadingAgent
                  ? "Carregando instruções salvas..."
                  : "Instruções usadas pelo modelo em cada conversa com este agente."}
              </small>
            </label>

            <label className="mdc-chat-ws-field mdc-chat-agent-builder__field--compact">
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
            <h2 className="mdc-chat-ws-section-head">Conhecimento</h2>

            {agent ? (
              <>
                {onOpenRagAdmin ? (
                  <button
                    type="button"
                    className="mdc-chat-ws-outline-btn"
                    onClick={() => onOpenRagAdmin(agent.id)}
                  >
                    Especialização RAG (admin)
                  </button>
                ) : null}

                <AgentKnowledgeSourcesPanel
                  sources={agentSources}
                  isUploading={isSavingSource}
                  notice={sourceNotice}
                  onUploadFiles={uploadAgentKnowledgeFiles}
                  onLocalDuplicatesSkipped={(count) =>
                    setSourceNotice(
                      count === 1
                        ? "Este arquivo já está neste agente (mesmo conteúdo)."
                        : `${count} arquivo(s) ignorado(s): conteúdo já existente.`,
                    )
                  }
                  onRemoveSource={removeAgentSource}
                  onDownloadSource={downloadAgentSource}
                  noteSlot={
                    <details className="mdc-chat-ws-details">
                      <summary>Adicionar nota de texto</summary>
                      <div className="mdc-chat-ws-details-body">
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
                            className="mdc-chat-ws-outline-btn"
                            disabled={isSavingSource || !sourceContent.trim()}
                            onClick={() => void createAgentKnowledgeNote()}
                          >
                            Adicionar nota
                          </button>
                        </div>
                      </div>
                    </details>
                  }
                />
              </>
            ) : (
              <p className="mdc-chat-ws-empty">Salve o agente para adicionar arquivos e notas.</p>
            )}
          </section>

          <section className="mdc-chat-agent-builder__section">
            <h2 className="mdc-chat-ws-section-head">Recursos</h2>

            <div className="mdc-chat-agent-builder__resource-list">
              <AgentBuilderCheckbox
                checked={capActions}
                onChange={(event) => setCapActions(event.target.checked)}
                label="Permitir uso de actions configuradas"
              />
              <AgentBuilderCheckbox
                checked={capFiles}
                onChange={(event) => setCapFiles(event.target.checked)}
                label="Permitir documentos e fontes de conhecimento"
              />
              <AgentBuilderCheckbox
                checked={capCanvas}
                onChange={(event) => setCapCanvas(event.target.checked)}
                label="Permitir lousa (canvas)"
              />
            </div>
          </section>

          <section className="mdc-chat-agent-builder__section">
            <h2 className="mdc-chat-ws-section-head">Skills</h2>
            <p className="mdc-chat-ws-section-lead">
              Comportamentos no prompt. Actions executam APIs externas.
            </p>

            {agent ? (
              <div className="mdc-chat-agent-builder__skills-panel">
                {agentSkillBindings.length > 0 ? (
                  <div className="mdc-chat-ws-list">
                    {agentSkillBindings.map((binding) => (
                      <article
                        key={binding.skillKey}
                        className="mdc-chat-ws-list-row mdc-chat-agent-builder__skill-row"
                      >
                        <span className="mdc-chat-ws-list-row__icon">
                          <Sparkles size={18} aria-hidden="true" />
                        </span>
                        <div className="mdc-chat-ws-list-row__copy">
                          <strong>{binding.label}</strong>
                          <small>{binding.skillKey}</small>
                        </div>
                        <span className="mdc-chat-agent-builder__skill-meta">
                          <em
                            className={
                              binding.enabled
                                ? "mdc-chat-agent-builder__skill-pill mdc-chat-agent-builder__skill-pill--on"
                                : "mdc-chat-agent-builder__skill-pill"
                            }
                          >
                            {binding.enabled ? "Ativa" : "Inativa"}
                          </em>
                          {binding.skillKey === "sql" ? (
                            <em
                              className={
                                binding.derived?.sqlExecutionAvailable
                                  ? "mdc-chat-agent-builder__skill-pill mdc-chat-agent-builder__skill-pill--on"
                                  : "mdc-chat-agent-builder__skill-pill"
                              }
                            >
                              {binding.derived?.sqlExecutionAvailable
                                ? "SQL no banco"
                                : "Sem action SQL"}
                            </em>
                          ) : null}
                        </span>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="mdc-chat-ws-empty">
                    Nenhuma skill configurada. Ative comportamentos no assistente.
                  </p>
                )}

                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  onClick={() => onConfigureSkills?.(agent)}
                >
                  <Settings2 size={16} aria-hidden="true" />
                  <span>Configurar skills</span>
                </button>
              </div>
            ) : (
              <p className="mdc-chat-ws-empty">
                Salve o agente para configurar skills (ex.: Especialista SQL).
              </p>
            )}
          </section>

          <section className="mdc-chat-agent-builder__section">
            <h2 className="mdc-chat-ws-section-head">Ações</h2>
            <p className="mdc-chat-ws-section-lead">
              APIs OpenAPI vinculadas a este agente.
            </p>

            {agent ? (
              <div className="mdc-chat-agent-builder__actions-panel">
                {agentActionProviders.length > 0 ? (
                  <div className="mdc-chat-ws-list mdc-chat-agent-builder__action-list">
                    {agentActionProviders.map((provider) => (
                      <article key={provider.providerKey} className="mdc-chat-ws-list-row">
                        <span className="mdc-chat-ws-list-row__icon">
                          <Zap size={18} aria-hidden="true" />
                        </span>
                        <div className="mdc-chat-ws-list-row__copy">
                          <strong>{provider.providerName || provider.providerKey}</strong>
                          <small>
                            {provider.providerKey}
                            {provider.enabled ? " · ativo" : " · desativado"}
                            {` · ${provider.actionCount} rota(s)`}
                          </small>
                        </div>
                        <div className="mdc-chat-agent-builder__action-list-actions">
                          <AgentBuilderSwitch
                            size="compact"
                            checked={provider.enabled}
                            disabled={actionProviderBusyKey === provider.providerKey}
                            onChange={(event) =>
                              void toggleAgentActionProvider(provider, event.target.checked)
                            }
                            ariaLabel={
                              provider.enabled
                                ? `Desativar ${provider.providerName || provider.providerKey}`
                                : `Ativar ${provider.providerName || provider.providerKey}`
                            }
                          />
                          <button
                            type="button"
                            onClick={() => onConfigureAction?.(agent, provider.providerKey)}
                            title="Configurar action"
                          >
                            <Settings2 size={16} aria-hidden="true" />
                          </button>
                          <button
                            type="button"
                            className="mdc-chat-agent-builder__action-delete"
                            title="Excluir action do agente"
                            disabled={actionProviderBusyKey === provider.providerKey}
                            onClick={() => void removeAgentActionProvider(provider)}
                          >
                            <Trash2 size={16} aria-hidden="true" />
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="mdc-chat-ws-empty">
                    Nenhuma action configurada. Crie uma API OpenAPI para este agente.
                  </p>
                )}

                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  onClick={() => onCreateAction?.(agent)}
                >
                  <Plus size={16} aria-hidden="true" />
                  <span>Criar nova ação</span>
                </button>
              </div>
            ) : (
              <p className="mdc-chat-ws-empty">
                Salve o agente para cadastrar actions e escolher rotas.
              </p>
            )}
          </section>

          <div className="mdc-chat-agent-builder__advanced">
          {agent?.id && agentVersions.length > 0 ? (
            <section className="mdc-chat-agent-builder__section">
              <h2 className="mdc-chat-ws-section-head">Versões publicadas</h2>
              <ul className="mdc-chat-agent-builder__version-list">
                {agentVersions.map((version) => (
                  <li key={version.id}>
                    <strong>v{version.version}</strong>
                    <span>{version.event}</span>
                    {version.createdAt ? (
                      <time>{new Date(version.createdAt).toLocaleString("pt-BR")}</time>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {agent && ["owner", "editor", "system"].includes(agent.access_role) ? (
            <section className="mdc-chat-agent-builder__section mdc-chat-agent-builder__usage-panel">
              <details className="mdc-chat-agent-builder__usage-details">
                <summary className="mdc-chat-ws-section-head">Uso (últimos 7 dias)</summary>

                <div className="mdc-chat-agent-builder__usage-details-body">
                  {isLoadingStats ? (
                    <p className="mdc-chat-muted">Carregando estatísticas...</p>
                  ) : agentStats?.miniDashboard ? (
                    <AgentMiniDashboard stats={agentStats} compact />
                  ) : agentStats ? (
                    <p className="mdc-chat-muted">Estatísticas sem painel visual (atualize a API).</p>
                  ) : (
                    <p className="mdc-chat-muted">Sem dados de uso no período.</p>
                  )}
                </div>
              </details>

              {agent.access_role === "owner" ? (
                <div className="mdc-chat-agent-builder__resource-list">
                  <AgentBuilderCheckbox
                    checked={copyActionsOnDuplicate}
                    onChange={(event) => setCopyActionsOnDuplicate(event.target.checked)}
                    label="Ao duplicar, copiar também APIs e actions configuradas"
                  />
                  <AgentBuilderCheckbox
                    checked={copySourcesOnDuplicate}
                    onChange={(event) => setCopySourcesOnDuplicate(event.target.checked)}
                    label="Ao duplicar, copiar também fontes de conhecimento do agente"
                  />
                </div>
              ) : null}
            </section>
          ) : null}

          <section className="mdc-chat-agent-builder__section">
            <h2 className="mdc-chat-ws-section-head">Execução</h2>

            <AgentBuilderCheckbox
              checked={enabled}
              onChange={(event) => setEnabled(event.target.checked)}
              label="Agente ativo (visível para uso)"
            />

            <label className="mdc-chat-ws-field mdc-chat-agent-builder__field--compact">
              <span>Máximo de chamadas de ferramentas</span>
              <input
                type="number"
                min={1}
                max={20}
                value={maxToolCalls}
                onChange={(event) =>
                  setMaxToolCalls(Math.max(1, Math.min(20, Number(event.target.value) || 5)))
                }
              />
            </label>

            <AgentBuilderCheckbox
              checked={requiresConfirmationForWrite}
              onChange={(event) =>
                setRequiresConfirmationForWrite(event.target.checked)
              }
              label="Exigir confirmação para ações de escrita"
            />
          </section>

          {agent?.access_role === "owner" ? (
            <section className="mdc-chat-agent-builder__section">
              <h2 className="mdc-chat-ws-section-head">Compartilhamento</h2>

              <div className="mdc-chat-agent-builder__grid">
                <ChatUserSearchField
                  value={shareTargetUserId}
                  onChange={setShareTargetUserId}
                  getAccessToken={getAccessToken}
                  disabled={isSharing}
                />

                <label>
                  <span>Papel</span>
                  <select
                    value={shareRole}
                    onChange={(event) =>
                      setShareRole(event.target.value as "viewer" | "editor")
                    }
                  >
                    <option value="viewer">Visualizador</option>
                    <option value="editor">Editor</option>
                  </select>
                </label>
              </div>

              <button
                type="button"
                disabled={isSharing}
                onClick={() => void shareCurrentAgent()}
              >
                {isSharing ? "Compartilhando..." : "Compartilhar agente"}
              </button>

              {shareMessage ? <p className="mdc-chat-muted">{shareMessage}</p> : null}

              <div className="mdc-chat-agent-builder__share-list">
                {isLoadingShares ? (
                  <p className="mdc-chat-muted">Carregando compartilhamentos...</p>
                ) : agentShares.length === 0 ? (
                  <p className="mdc-chat-muted">Nenhum compartilhamento ativo.</p>
                ) : (
                  agentShares.map((share) => (
                    <article key={share.id}>
                      <span>
                        <strong>
                          {share.target_user_name ||
                            share.target_user_email ||
                            share.target_user_id}
                        </strong>
                        {share.target_user_email ? (
                          <small>{share.target_user_email}</small>
                        ) : null}
                      </span>
                      <select
                        value={share.role}
                        disabled={updatingShareUserId === share.target_user_id}
                        onChange={(event) =>
                          void updateAgentShareRole(
                            share.target_user_id,
                            event.target.value as "viewer" | "editor",
                          )
                        }
                        aria-label="Papel do compartilhamento"
                      >
                        <option value="viewer">Visualizador</option>
                        <option value="editor">Editor</option>
                      </select>
                      <button
                        type="button"
                        disabled={revokingShareUserId === share.target_user_id}
                        onClick={() => void revokeAgentShare(share.target_user_id)}
                      >
                        {revokingShareUserId === share.target_user_id
                          ? "Revogando..."
                          : "Revogar"}
                      </button>
                    </article>
                  ))
                )}
              </div>

              <div className="mdc-chat-agent-builder__transfer">
                <h3>Transferir propriedade</h3>
                <p>Defina outro usuário como dono deste agente.</p>
                <ChatUserSearchField
                  value={transferTargetUserId}
                  onChange={setTransferTargetUserId}
                  getAccessToken={getAccessToken}
                  disabled={isTransferring}
                />
                <button
                  type="button"
                  className="mdc-chat-ws-outline-btn"
                  disabled={isTransferring}
                  onClick={() => void transferAgentOwnership()}
                >
                  {isTransferring ? "Transferindo..." : "Transferir propriedade"}
                </button>
                {transferMessage ? <p className="mdc-chat-muted">{transferMessage}</p> : null}
              </div>
            </section>
          ) : null}
          </div>

            </>
          )}
          </ChatAnimatedPanel>

          {localError ? (
            <p className="mdc-chat-agent-builder__error">{localError}</p>
          ) : null}
          </div>
        </form>

        {splitEnabled ? (
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Ajustar largura da pré-visualização"
            className={
              isDragging
                ? "mdc-chat-agent-builder__splitter is-dragging"
                : "mdc-chat-agent-builder__splitter"
            }
            onPointerDown={onSplitterPointerDown}
          />
        ) : null}

        <aside className="mdc-chat-agent-builder__preview">
          <div className="mdc-chat-agent-builder__preview-label">
            <span>Pré-visualizar</span>
            <span className="mdc-chat-agent-builder__preview-model">
              Rascunho local · não afeta usuários
            </span>
          </div>

          <div className="mdc-chat-agent-builder__preview-card">
            <div className="mdc-chat-agent-builder__preview-avatar">
              <Bot size={26} aria-hidden="true" />
            </div>

            <h2>{name.trim() || "Novo agente"}</h2>

            <p>
              {description.trim() ||
                "Configure comportamento, instruções e quebra-gelos deste especialista."}
            </p>

            {previewIcebreakers.length > 0 ? (
              <div
                className={[
                  "mdc-chat-agent-builder__preview-icebreakers",
                  previewIcebreakerDensityClass,
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {usingDefaultPreviewIcebreakers ? (
                  <p className="mdc-chat-agent-builder__preview-icebreakers-hint">
                    Sugestões padrão — configure em Quebra-gelos ou clique para testar.
                  </p>
                ) : null}
                {previewIcebreakers.slice(0, 3).map((icebreaker) => (
                  <button
                    key={icebreaker}
                    type="button"
                    disabled={isPreviewLoading}
                    title={icebreaker}
                    onClick={() => void sendPreviewMessage(icebreaker)}
                  >
                    {formatIcebreakerForDisplay(icebreaker)}
                  </button>
                ))}
              </div>
            ) : null}

            {previewMessages.length > 0 ? (
              <div className="mdc-chat-agent-builder__preview-messages">
                {previewMessages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={
                      message.role === "user"
                        ? "mdc-chat-agent-builder__preview-message mdc-chat-agent-builder__preview-message--user"
                        : "mdc-chat-agent-builder__preview-message"
                    }
                  >
                    {message.content}
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mdc-chat-agent-builder__preview-input">
              <input
                value={previewInput}
                onChange={(event) => setPreviewInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void sendPreviewMessage();
                  }
                }}
                placeholder="Pergunte alguma coisa"
                disabled={isPreviewLoading}
              />
              <button
                type="button"
                disabled={isPreviewLoading}
                onClick={() => void sendPreviewMessage()}
              >
                <Send size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
