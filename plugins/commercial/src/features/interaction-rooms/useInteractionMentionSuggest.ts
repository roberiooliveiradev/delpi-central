import { useCallback, useEffect, useRef, useState } from "react";

import { suggestInteractionMentions } from "../../api/interactionRoomsApi";
import {
  mapSuggestItemsToMentionHits,
  mentionHitToPayload,
  mentionsPresentInBody,
  type InteractionMentionHit,
  type InteractionMentionPayload,
} from "./mentionSuggestAdapter";

const SUGGEST_DEBOUNCE_MS = 220;

/**
 * Busca menções na commercial-api e mantém payload para o POST da mensagem.
 */
export function useInteractionMentionSuggest() {
  const [hits, setHits] = useState<InteractionMentionHit[]>([]);
  const pendingRef = useRef<InteractionMentionPayload[]>([]);
  const queryRef = useRef<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const clearTimer = () => {
    if (timerRef.current != null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      clearTimer();
      abortRef.current?.abort();
    };
  }, []);

  const onMentionQueryChange = useCallback((query: string | null) => {
    queryRef.current = query;
    clearTimer();
    abortRef.current?.abort();
    if (query == null) {
      setHits([]);
      return;
    }
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      const controller = new AbortController();
      abortRef.current = controller;
      void (async () => {
        try {
          const items = await suggestInteractionMentions({
            q: query,
            limit: 12,
            signal: controller.signal,
          });
          if (controller.signal.aborted || queryRef.current !== query) return;
          setHits(mapSuggestItemsToMentionHits(items));
        } catch {
          if (controller.signal.aborted) return;
          if (queryRef.current === query) setHits([]);
        }
      })();
    }, SUGGEST_DEBOUNCE_MS);
  }, []);

  const onMentionInserted = useCallback((hit: InteractionMentionHit) => {
    pendingRef.current = [...pendingRef.current, mentionHitToPayload(hit)];
  }, []);

  const takeMentionsForBody = useCallback((body: string): InteractionMentionPayload[] => {
    const selected = mentionsPresentInBody(body, pendingRef.current);
    pendingRef.current = [];
    return selected;
  }, []);

  const resetMentions = useCallback(() => {
    pendingRef.current = [];
    setHits([]);
  }, []);

  return {
    hits,
    onMentionQueryChange,
    onMentionInserted,
    takeMentionsForBody,
    resetMentions,
  };
}
