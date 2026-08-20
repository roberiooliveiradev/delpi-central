import { useCallback, useMemo, useState } from "react";

import {
  clearInteractionMessageReaction,
  setInteractionMessageReaction,
  type InteractionReactionDto,
} from "../../api/interactionRoomsApi";
import {
  CM_PORTAL_SCOPE,
  CommercialReactionBar,
  CommercialReactionQuickBar,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import {
  aggregateMessageReactions,
  applyLocalReactionToggle,
} from "./interactionRoomReactions";

type ReactionHostProps = {
  roomId: string;
  messageId: string;
  reactions: readonly InteractionReactionDto[];
  sessionUserId: string | null;
  disabled?: boolean;
  onReactionsChange: (
    messageId: string,
    reactions: InteractionReactionDto[],
  ) => void;
  onError: (message: string) => void;
};

function useInteractionRoomReactionToggle({
  roomId,
  messageId,
  reactions,
  sessionUserId,
  disabled = false,
  onReactionsChange,
  onError,
}: ReactionHostProps) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [busyCode, setBusyCode] = useState<string | null>(null);
  const items = useMemo(
    () => aggregateMessageReactions(reactions, sessionUserId),
    [reactions, sessionUserId],
  );
  const activeCodes = useMemo(
    () =>
      new Set(
        items.filter((item) => item.reactedByMe).map((item) => item.code),
      ),
    [items],
  );

  const toggle = useCallback(
    async (code: string) => {
      const id = roomId.trim();
      const mid = messageId.trim();
      const uid = (sessionUserId || "").trim();
      const reactionCode = code.trim();
      if (!id || !mid || !uid || !reactionCode || disabled || busyCode) return;
      const current = items.find((item) => item.code === reactionCode);
      const nextActive = !current?.reactedByMe;
      const previous = [...reactions];
      onReactionsChange(
        mid,
        applyLocalReactionToggle(previous, {
          messageId: mid,
          userId: uid,
          code: reactionCode,
          nextActive,
        }),
      );
      setBusyCode(reactionCode);
      try {
        if (nextActive) {
          await setInteractionMessageReaction(id, mid, reactionCode);
        } else {
          await clearInteractionMessageReaction(id, mid, reactionCode);
        }
      } catch (err: unknown) {
        onReactionsChange(mid, previous);
        onError(
          err instanceof Error ? err.message : content.reactionError,
        );
      } finally {
        setBusyCode(null);
      }
    },
    [
      roomId,
      messageId,
      sessionUserId,
      disabled,
      busyCode,
      items,
      reactions,
      onReactionsChange,
      onError,
      content.reactionError,
    ],
  );

  return {
    content,
    items,
    activeCodes,
    busy: Boolean(busyCode) || disabled,
    toggle,
  };
}

/**
 * Chips agregados abaixo do body (sem «+» — picker fica na barra de opções).
 */
export function InteractionRoomMessageReactions(props: ReactionHostProps) {
  const { content, items, busy, toggle } = useInteractionRoomReactionToggle(props);
  if (props.disabled || items.length === 0) return null;

  return (
    <div className="cm-room-thread__message-reactions">
      <CommercialReactionBar
        listAriaLabel={content.reactionsAriaLabel}
        items={items}
        onToggle={(code) => {
          void toggle(code);
        }}
        /* Sem emojiAdd: adição só na ReactionQuickBar da toolbar. */
      />
    </div>
  );
}

/**
 * 5 emojis rápidos + «+» (catálogo) na barra de opções do MessageThread.
 */
export function InteractionRoomMessageReactionQuickBar(props: ReactionHostProps) {
  const { content, activeCodes, busy, toggle } = useInteractionRoomReactionToggle(
    props,
  );
  if (props.disabled) return null;

  return (
    <CommercialReactionQuickBar
      listAriaLabel={content.reactionsAriaLabel}
      addAriaLabel={content.reactionAddAriaLabel}
      emojiMenuAriaLabel={content.reactionEmojiMenuAriaLabel}
      activeCodes={activeCodes}
      disabled={busy}
      portalScopeClassName={CM_PORTAL_SCOPE}
      onPick={(code) => {
        void toggle(code);
      }}
    />
  );
}
