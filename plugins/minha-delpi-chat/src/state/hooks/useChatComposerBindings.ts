import { useMemo, useState } from "react";

import type { ChatAgent, ChatProject } from "../../data/api/chatTypes";
import { getTypingCorrectionContent } from "../../content/messageComposerContent";
import {
  formatComposerPlaceholderParts,
  resolveComposerContextBarFromLists,
  resolveEffectiveAgentIds,
  resolveEffectiveProjectIds,
} from "../chatComposerContext";
import type { ChatInputAttachment } from "../../ui/components/composer/ChatInput";
import { useChatPresentationFormat } from "./useChatPresentationFormat";
import { useChatResponseMode } from "./useChatResponseMode";
import { useChatTypingCorrection } from "./useChatTypingCorrection";

type UseChatComposerBindingsOptions = {
  sessionId: string | null;
  draft: string;
  onDraftChange: (value: string) => void;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  agents?: ChatAgent[];
  projects?: ChatProject[];
  pageAgentId?: string | null;
  pageProjectId?: string | null;
  sessionAgentId?: string | null;
  sessionProjectId?: string | null;
  contextAgentIds?: string[];
  contextProjectIds?: string[];
  excludedAgentIds?: string[];
  excludedProjectIds?: string[];
  isNarrow?: boolean;
  onToggleAgent?: (agentId: string) => void;
  onRemoveContextAgent?: (agentId: string) => void;
  onOpenAgentPage?: (agentId: string) => void;
  onToggleProject?: (projectId: string) => void;
  onRemoveContextProject?: (projectId: string) => void;
};

export function useChatComposerBindings({
  sessionId,
  draft,
  onDraftChange,
  getAccessToken,
  agents = [],
  projects = [],
  pageAgentId = null,
  pageProjectId = null,
  sessionAgentId = null,
  sessionProjectId = null,
  contextAgentIds = [],
  contextProjectIds = [],
  excludedAgentIds = [],
  excludedProjectIds = [],
  isNarrow = false,
  onToggleAgent,
  onRemoveContextAgent,
  onOpenAgentPage,
  onToggleProject,
  onRemoveContextProject,
}: UseChatComposerBindingsOptions) {
  const [composerAttachments, setComposerAttachments] = useState<ChatInputAttachment[]>([]);

  const {
    enabled: responseModesEnabled,
    modes: responseModes,
    responseMode,
    setResponseMode,
  } = useChatResponseMode({ getAccessToken });

  const {
    options: presentationFormatOptions,
    presentationFormat,
    setPresentationFormat,
  } = useChatPresentationFormat({
    sessionId,
    getAccessToken,
  });

  const typingCorrectionLabels = useMemo(() => getTypingCorrectionContent(), []);
  const {
    suggestion: typingSuggestion,
    dismissSuggestion: dismissTypingSuggestionState,
  } = useChatTypingCorrection({
    draft,
    sessionId,
    enabled: true,
    getAccessToken,
  });

  const effectiveAgentIds = useMemo(
    () =>
      resolveEffectiveAgentIds({
        pageAgentId,
        sessionAgentId,
        contextAgentIds,
        excludedAgentIds,
      }),
    [contextAgentIds, excludedAgentIds, pageAgentId, sessionAgentId],
  );

  const effectiveProjectIds = useMemo(
    () =>
      resolveEffectiveProjectIds({
        pageProjectId,
        sessionProjectId,
        contextProjectIds,
        excludedProjectIds,
      }),
    [contextProjectIds, excludedProjectIds, pageProjectId, sessionProjectId],
  );

  const effectiveComposerProjects = useMemo(
    () =>
      effectiveProjectIds
        .map((id) => projects.find((project) => project.id === id))
        .filter((project): project is ChatProject => Boolean(project)),
    [effectiveProjectIds, projects],
  );

  const effectiveComposerAgents = useMemo(
    () =>
      effectiveAgentIds
        .map((id) => agents.find((agent) => agent.id === id))
        .filter((agent): agent is ChatAgent => Boolean(agent)),
    [agents, effectiveAgentIds],
  );

  const placeholder = useMemo(() => {
    const combinedPlaceholder = formatComposerPlaceholderParts({
      projectNames: effectiveComposerProjects.map((item) => item.name),
      agentNames: effectiveComposerAgents.map((item) => item.name),
    });

    if (combinedPlaceholder) {
      if (isNarrow) {
        if (effectiveComposerProjects.length > 0 && effectiveComposerAgents.length > 0) {
          return "Chat com contexto combinado";
        }

        if (effectiveComposerProjects.length > 0) {
          return "Chat no projeto";
        }

        return "Pergunte ao agente";
      }

      return combinedPlaceholder;
    }

    return "O que vamos resolver hoje? Pode perguntar do seu jeito.";
  }, [effectiveComposerAgents, effectiveComposerProjects, isNarrow]);

  const composerContextBarItems = useMemo(
    () =>
      resolveComposerContextBarFromLists({
        pageAgentId,
        pageProjectId,
        sessionAgentId,
        sessionProjectId,
        contextAgentIds,
        contextProjectIds,
        excludedAgentIds,
        excludedProjectIds,
      }),
    [
      contextAgentIds,
      contextProjectIds,
      excludedAgentIds,
      excludedProjectIds,
      pageAgentId,
      pageProjectId,
      sessionAgentId,
      sessionProjectId,
    ],
  );

  function handleAttachFiles(files: File[]) {
    setComposerAttachments((current) => [
      ...current,
      ...files.map((file) => ({
        id: `composer-attachment-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        name: file.name,
        size: file.size,
        type: file.type,
        file,
        status: "queued" as const,
      })),
    ]);
  }

  function handleRemoveAttachment(attachmentId: string) {
    setComposerAttachments((current) => current.filter((item) => item.id !== attachmentId));
  }

  function handleClearAttachments() {
    setComposerAttachments([]);
  }

  function handleAcceptTypingSuggestion() {
    if (!typingSuggestion) {
      return;
    }

    onDraftChange(typingSuggestion.corrected);
    dismissTypingSuggestionState();
  }

  return {
    placeholder,
    composerAttachmentProps: {
      attachments: composerAttachments,
      onAttachFiles: handleAttachFiles,
      onRemoveAttachment: handleRemoveAttachment,
      onClearAttachments: handleClearAttachments,
      getAccessToken,
    },
    composerResponseModeProps: {
      showResponseModeSelector: responseModesEnabled,
      responseModes,
      responseMode,
      onResponseModeChange: setResponseMode,
    },
    composerPresentationFormatProps: {
      showPresentationFormatSelector: true,
      presentationFormatOptions,
      presentationFormat,
      onPresentationFormatChange: setPresentationFormat,
    },
    composerTypingCorrectionProps: {
      typingSuggestion,
      typingSuggestionLabels: typingCorrectionLabels,
      onAcceptTypingSuggestion: handleAcceptTypingSuggestion,
      onDismissTypingSuggestion: dismissTypingSuggestionState,
    },
    composerContextProps: {
      agents,
      projects,
      selectedAgentIds: effectiveAgentIds,
      selectedProjectIds: effectiveProjectIds,
      contextBadgeItems: composerContextBarItems,
      onToggleAgent,
      onRemoveContextAgent,
      onOpenAgentPage,
      onToggleProject,
      onRemoveContextProject,
    },
  };
}

export type ChatComposerBindings = ReturnType<typeof useChatComposerBindings>;
