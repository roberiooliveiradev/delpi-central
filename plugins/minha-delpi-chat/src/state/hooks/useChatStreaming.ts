import { useCallback, useRef, useState } from "react";

import { resendChatMessage, streamChatMessage } from "../../data/api/chatApi";
import type {
  ChatPlaybackEvent,
  ChatSource,
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
  agentKey?: string | null;
  onStatus?: (message: string) => void;
  onSources?: (sources: ChatSource[]) => void;
  onToolCalls?: (toolCalls: ChatToolCall[]) => void;
  onToken?: (token: string) => void;
  onAssistantPending?: (messageId: string) => void;
  onPlayback?: (payload: ChatPlaybackEvent) => void;
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
          | "onSources"
          | "onToolCalls"
          | "onToken"
          | "onAssistantPending"
          | "onPlayback"
          | "onDone"
          | "onError"
        >,
        signal: AbortSignal,
      ) => Promise<void>,
      callbacks: Pick<
        StreamMessageParams,
        | "onStatus"
        | "onSources"
        | "onToolCalls"
        | "onToken"
        | "onAssistantPending"
        | "onPlayback"
        | "onDone"
        | "onError"
      >,
    ) => {
      const abortController = new AbortController();
      streamsRef.current.set(sessionId, abortController);
      bumpStreams();

      try {
        await runner(callbacks, abortController.signal);
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
      agentKey,
      onStatus,
      onSources,
      onToolCalls,
      onToken,
      onAssistantPending,
      onPlayback,
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
              agentKey: agentKey ?? undefined,
            },
            streamCallbacks,
            {
              getAccessToken: options.getAccessToken,
              signal,
            },
          ),
        {
          onStatus,
          onSources,
          onToolCalls,
          onToken,
          onAssistantPending,
          onPlayback,
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
      onStatus,
      onSources,
      onToolCalls,
      onToken,
      onAssistantPending,
      onPlayback,
      onDone,
      onError,
    }: {
      sessionId: string;
      messageId: string;
      content: string;
      context?: string;
      onStatus?: (message: string) => void;
      onSources?: (sources: ChatSource[]) => void;
      onToolCalls?: (toolCalls: ChatToolCall[]) => void;
      onToken?: (token: string) => void;
      onAssistantPending?: (messageId: string) => void;
      onPlayback?: (payload: ChatPlaybackEvent) => void;
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
          }),
        {
          onStatus,
          onSources,
          onToolCalls,
          onToken,
          onAssistantPending,
          onPlayback,
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
