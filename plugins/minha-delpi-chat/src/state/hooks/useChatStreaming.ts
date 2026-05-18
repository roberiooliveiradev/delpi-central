import { useCallback, useRef, useState } from "react";

import { resendChatMessage, streamChatMessage } from "../../data/api/chatApi";
import type {
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
  onStatus?: (message: string) => void;
  onSources?: (sources: ChatSource[]) => void;
  onToolCalls?: (toolCalls: ChatToolCall[]) => void;
  onToken?: (token: string) => void;
  onDone?: (response: SendChatMessageResponse) => void;
  onError?: (message: string) => void;
};

export function useChatStreaming(options: UseChatStreamingOptions = {}) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const cancelStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsStreaming(false);
  }, []);

  const runStream = useCallback(
    async (
      runner: (
        callbacks: Pick<
          StreamMessageParams,
          "onStatus" | "onSources" | "onToolCalls" | "onToken" | "onDone" | "onError"
        >,
        signal: AbortSignal,
      ) => Promise<void>,
      callbacks: Pick<
        StreamMessageParams,
        "onStatus" | "onSources" | "onToolCalls" | "onToken" | "onDone" | "onError"
      >,
    ) => {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      setIsStreaming(true);

      try {
        await runner(callbacks, abortController.signal);
      } finally {
        abortControllerRef.current = null;
        setIsStreaming(false);
      }
    },
    [],
  );

  const streamMessage = useCallback(
    async ({
      sessionId,
      message,
      context,
      attachmentIds,
      onStatus,
      onSources,
      onToolCalls,
      onToken,
      onDone,
      onError,
    }: StreamMessageParams) => {
      await runStream(
        (streamCallbacks, signal) =>
          streamChatMessage(
            sessionId,
            {
              message,
              context,
              attachmentIds,
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
      onDone?: (response: SendChatMessageResponse) => void;
      onError?: (message: string) => void;
    }) => {
      await runStream(
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
          onDone,
          onError,
        },
      );
    },
    [options.getAccessToken, runStream],
  );

  return {
    isStreaming,
    streamMessage,
    resendMessage,
    cancelStreaming,
  };
}
