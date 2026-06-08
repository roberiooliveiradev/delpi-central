import { useCallback, useRef, useState } from "react";

import { resendChatMessage, streamChatMessage } from "../../data/api/chatApi";
import type {
  ChatCanvasOpenPayload,
  ChatPlaybackEvent,
  ChatResponseModeId,
  ChatSource,
  ChatStreamActivityEntry,
  ChatToolCall,
  SendChatMessageResponse,
} from "../../data/api/chatTypes";

type UseChatStreamingOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type StreamMessageParams = {
  sessionId: string;
  message: string;
  context?: string;
  attachmentIds?: string[];
  agentId?: string | null;
  agentIds?: string[];
  projectId?: string | null;
  projectIds?: string[];
  chatMode?: "common" | "agent";
  responseMode?: ChatResponseModeId;
  onStatus?: (message: string) => void;
  onActivity?: (entry: ChatStreamActivityEntry) => void;
  onSources?: (sources: ChatSource[]) => void;
  onToolCalls?: (toolCalls: ChatToolCall[]) => void;
  onToken?: (token: string) => void;
  onUserPersisted?: (messageId: string) => void;
  onSessionRenamed?: (title: string) => void;
  onAssistantPending?: (messageId: string) => void;
  onPlayback?: (payload: ChatPlaybackEvent) => void;
  onCanvasOpen?: (payload: ChatCanvasOpenPayload) => void;
  onDone?: (response: SendChatMessageResponse) => void;
  onError?: (message: string) => void;
};

export function useChatStreaming(options: UseChatStreamingOptions = {}) {
  const streamsRef = useRef<Map<string, AbortController>>(new Map());
  const [streamRevision, setStreamRevision] = useState(0);

  const bumpStreams = useCallback(() => {
    setStreamRevision((current) => current + 1);
  }, []);

  const isSessionStreaming = useCallback(
    (sessionId: string) => streamsRef.current.has(sessionId),
    [streamRevision],
  );

  const cancelSessionStreaming = useCallback(
    (sessionId: string) => {
      streamsRef.current.get(sessionId)?.abort();
      streamsRef.current.delete(sessionId);
      bumpStreams();
    },
    [bumpStreams],
  );

  const cancelStreaming = useCallback(
    (sessionId?: string) => {
      if (sessionId) {
        cancelSessionStreaming(sessionId);
        return;
      }

      for (const controller of streamsRef.current.values()) {
        controller.abort();
      }

      streamsRef.current.clear();
      bumpStreams();
    },
    [bumpStreams, cancelSessionStreaming],
  );

  const runStream = useCallback(
    async (
      sessionId: string,
      runner: (
        callbacks: Pick<
          StreamMessageParams,
          | "onStatus"
          | "onActivity"
          | "onSources"
          | "onToolCalls"
          | "onToken"
          | "onUserPersisted"
          | "onSessionRenamed"
          | "onAssistantPending"
          | "onPlayback"
          | "onCanvasOpen"
          | "onDone"
          | "onError"
        >,
        signal: AbortSignal,
      ) => Promise<void>,
      callbacks: Pick<
        StreamMessageParams,
        | "onStatus"
        | "onActivity"
        | "onSources"
        | "onToolCalls"
        | "onToken"
        | "onUserPersisted"
        | "onSessionRenamed"
        | "onAssistantPending"
        | "onPlayback"
        | "onCanvasOpen"
        | "onDone"
        | "onError"
      >,
    ) => {
      const abortController = new AbortController();
      streamsRef.current.set(sessionId, abortController);
      bumpStreams();

      try {
        await runner(callbacks, abortController.signal);
      } catch (error) {
        if (
          abortController.signal.aborted ||
          (error instanceof DOMException && error.name === "AbortError")
        ) {
          throw new DOMException("The operation was aborted.", "AbortError");
        }

        throw error;
      } finally {
        streamsRef.current.delete(sessionId);
        bumpStreams();
      }
    },
    [bumpStreams],
  );

  const streamMessage = useCallback(
    async ({
      sessionId,
      message,
      context,
      attachmentIds,
      agentId,
      agentIds,
      projectId,
      projectIds,
      chatMode,
      responseMode,
      onStatus,
      onActivity,
      onSources,
      onToolCalls,
      onToken,
      onUserPersisted,
      onSessionRenamed,
      onAssistantPending,
      onPlayback,
      onCanvasOpen,
      onDone,
      onError,
    }: StreamMessageParams) => {
      await runStream(
        sessionId,
        (streamCallbacks, signal) =>
          streamChatMessage(
            sessionId,
            {
              message,
              context,
              attachmentIds,
              agentId: agentId ?? undefined,
              agentIds: agentIds && agentIds.length > 0 ? agentIds : undefined,
              projectId: projectId ?? null,
              projectIds: projectIds && projectIds.length > 0 ? projectIds : undefined,
              chatMode,
              responseMode,
            },
            streamCallbacks,
            {
              getAccessToken: options.getAccessToken,
              signal,
            },
          ),
        {
          onStatus,
          onActivity,
          onSources,
          onToolCalls,
          onToken,
          onUserPersisted,
          onSessionRenamed,
          onAssistantPending,
          onPlayback,
          onCanvasOpen,
          onDone,
          onError,
        },
      );
    },
    [options.getAccessToken, runStream],
  );

  const resendMessage = useCallback(
    async ({
      sessionId,
      messageId,
      content,
      context,
      responseMode,
      onStatus,
      onActivity,
      onSources,
      onToolCalls,
      onToken,
      onAssistantPending,
      onPlayback,
      onCanvasOpen,
      onDone,
      onError,
    }: {
      sessionId: string;
      messageId: string;
      content: string;
      context?: string;
      responseMode?: ChatResponseModeId;
      onStatus?: (message: string) => void;
      onActivity?: (entry: ChatStreamActivityEntry) => void;
      onSources?: (sources: ChatSource[]) => void;
      onToolCalls?: (toolCalls: ChatToolCall[]) => void;
      onToken?: (token: string) => void;
      onAssistantPending?: (messageId: string) => void;
      onPlayback?: (payload: ChatPlaybackEvent) => void;
      onCanvasOpen?: (payload: ChatCanvasOpenPayload) => void;
      onDone?: (response: SendChatMessageResponse) => void;
      onError?: (message: string) => void;
    }) => {
      await runStream(
        sessionId,
        (streamCallbacks, signal) =>
          resendChatMessage(sessionId, messageId, content, streamCallbacks, {
            getAccessToken: options.getAccessToken,
            signal,
            context,
            responseMode,
          }),
        {
          onStatus,
          onActivity,
          onSources,
          onToolCalls,
          onToken,
          onAssistantPending,
          onPlayback,
          onCanvasOpen,
          onDone,
          onError,
        },
      );
    },
    [options.getAccessToken, runStream],
  );

  return {
    isSessionStreaming,
    streamMessage,
    resendMessage,
    cancelStreaming,
    cancelSessionStreaming,
  };
}
