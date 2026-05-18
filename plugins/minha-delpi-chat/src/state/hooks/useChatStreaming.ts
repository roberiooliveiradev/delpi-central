import { useCallback, useRef, useState } from "react";

import { streamChatMessage } from "../../data/api/chatApi";
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
      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      setIsStreaming(true);

      try {
        await streamChatMessage(
          sessionId,
          {
            message,
            context,
            attachmentIds,
          },
          {
            onStatus,
            onSources,
            onToolCalls,
            onToken,
            onDone,
            onError,
          },
          {
            getAccessToken: options.getAccessToken,
            signal: abortController.signal,
          },
        );
      } finally {
        abortControllerRef.current = null;
        setIsStreaming(false);
      }
    },
    [options.getAccessToken],
  );

  return {
    isStreaming,
    streamMessage,
    cancelStreaming,
  };
}
