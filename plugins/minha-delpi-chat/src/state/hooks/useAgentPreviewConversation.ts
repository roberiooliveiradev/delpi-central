import { useCallback, useEffect, useRef, useState } from "react";

import { previewChatAgent, previewChatAgentDraft } from "../../data/api/chatApi";
import type {
  ChatAgentPreviewDraft,
  ChatAgentPreviewResponse,
  ChatMessage,
  ChatStreamActivityEntry,
  ChatToolCall,
} from "../../data/api/chatTypes";
import {
  buildAgentPreviewAssistantMessage,
  buildPreviewActivityLogFromResult,
  createAgentPreviewChatMessage,
  createPreviewLoadingActivityLog,
  PREVIEW_REQUEST_TIMEOUT_MS,
  toPreviewPreviousMessages,
} from "../../ui/agentPreviewMessages";
import { resolveStreamingHeadline } from "../utils/streamingActivityLog";

type UseAgentPreviewConversationOptions = {
  agentId?: string | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  buildDraft: () => ChatAgentPreviewDraft;
  validateDraft?: () => string | null;
};

export function useAgentPreviewConversation({
  agentId,
  getAccessToken,
  buildDraft,
  validateDraft,
}: UseAgentPreviewConversationOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [streamingToolCalls, setStreamingToolCalls] = useState<ChatToolCall[]>([]);
  const [streamingActivityLog, setStreamingActivityLog] = useState<ChatStreamActivityEntry[]>(
    [],
  );
  const [streamingStatus, setStreamingStatus] = useState<string | null>(null);
  const phaseTimerRef = useRef<number | null>(null);
  const requestAbortRef = useRef<AbortController | null>(null);

  const clearPhaseTimer = useCallback(() => {
    if (phaseTimerRef.current !== null) {
      window.clearInterval(phaseTimerRef.current);
      phaseTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearPhaseTimer();
      requestAbortRef.current?.abort();
    };
  }, [clearPhaseTimer]);

  const startLoadingActivity = useCallback(() => {
    let phaseIndex = 0;

    const pushPhase = (index: number) => {
      const nextLog = createPreviewLoadingActivityLog(index);
      setStreamingActivityLog(nextLog);
      setStreamingStatus(resolveStreamingHeadline(null, nextLog));
    };

    pushPhase(phaseIndex);
    clearPhaseTimer();

    phaseTimerRef.current = window.setInterval(() => {
      if (phaseIndex >= 3) {
        clearPhaseTimer();
        return;
      }

      phaseIndex += 1;
      pushPhase(phaseIndex);
    }, 1800);
  }, [clearPhaseTimer]);

  const finishWithAssistantMessage = useCallback((result: ChatAgentPreviewResponse) => {
    const assistantMessage = buildAgentPreviewAssistantMessage(result);
    const activityLog = buildPreviewActivityLogFromResult(result);
    const toolCalls = assistantMessage.metadata?.toolCalls ?? [];

    setStreamingAnswer(assistantMessage.content);
    setStreamingToolCalls(toolCalls);
    setStreamingActivityLog(activityLog);
    setStreamingStatus(resolveStreamingHeadline(null, activityLog));

    window.requestAnimationFrame(() => {
      setMessages((current) => [...current, assistantMessage]);
      setStreamingAnswer("");
      setStreamingToolCalls([]);
      setStreamingActivityLog([]);
      setStreamingStatus(null);
      setIsSending(false);
    });
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      const message = content.trim();

      if (!message || isSending) {
        return;
      }

      if (!getAccessToken) {
        return;
      }

      const draftValidationError = validateDraft?.() ?? null;

      if (draftValidationError) {
        setMessages((current) => [
          ...current,
          createAgentPreviewChatMessage("assistant", draftValidationError),
        ]);
        return;
      }

      const previewDraft = buildDraft();
      const previousMessages = toPreviewPreviousMessages(messages);

      requestAbortRef.current?.abort();
      const controller = new AbortController();
      requestAbortRef.current = controller;
      const timeoutId = window.setTimeout(() => controller.abort(), PREVIEW_REQUEST_TIMEOUT_MS);

      setMessages((current) => [...current, createAgentPreviewChatMessage("user", message)]);
      setDraft("");
      setIsSending(true);
      setStreamingAnswer("");
      setStreamingToolCalls([]);
      startLoadingActivity();

      try {
        const result = agentId
          ? await previewChatAgent(
              agentId,
              {
                message,
                generateAnswer: true,
                executeToolsInSandbox: true,
                draft: previewDraft,
                previousMessages,
              },
              { getAccessToken, signal: controller.signal },
            )
          : await previewChatAgentDraft(
              {
                message,
                generateAnswer: true,
                executeToolsInSandbox: true,
                draft: previewDraft,
                previousMessages,
              },
              { getAccessToken, signal: controller.signal },
            );

        clearPhaseTimer();
        finishWithAssistantMessage(result);
      } catch {
        clearPhaseTimer();
        setStreamingAnswer("");
        setStreamingToolCalls([]);
        setStreamingActivityLog([]);
        setStreamingStatus(null);
        setIsSending(false);

        const isTimeout = controller.signal.aborted;
        setMessages((current) => [
          ...current,
          createAgentPreviewChatMessage(
            "assistant",
            isTimeout
              ? "A pré-visualização demorou demais. Tente uma pergunta mais curta ou verifique se o serviço de IA está disponível."
              : "Não foi possível gerar a pré-visualização com o rascunho atual.",
          ),
        ]);
      } finally {
        window.clearTimeout(timeoutId);

        if (requestAbortRef.current === controller) {
          requestAbortRef.current = null;
        }
      }
    },
    [
      agentId,
      buildDraft,
      clearPhaseTimer,
      finishWithAssistantMessage,
      getAccessToken,
      isSending,
      messages,
      startLoadingActivity,
      validateDraft,
    ],
  );

  return {
    messages,
    draft,
    setDraft,
    isSending,
    sendMessage,
    streamingAnswer,
    streamingToolCalls,
    streamingActivityLog,
    streamingStatus,
  };
}
