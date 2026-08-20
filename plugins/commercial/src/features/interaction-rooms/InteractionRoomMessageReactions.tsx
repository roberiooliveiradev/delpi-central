import { useCallback, useMemo, useState } from "react";

import {
  clearInteractionMessageReaction,
  setInteractionMessageReaction,
  type InteractionReactionDto,
} from "../../api/interactionRoomsApi";
import {
  CM_PORTAL_SCOPE,
  CommercialReactionBar,
} from "../../app/commercialUi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import {
  aggregateMessageReactions,
  applyLocalReactionToggle,
} from "./interactionRoomReactions";

type Props = {
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

/**
 * Chips de reação + «+» (EmojiInsertMenu no kit). Toggle chama PUT/DELETE na commercial-api.
 */
export function InteractionRoomMessageReactions({
  roomId,
  messageId,
  reactions,
  sessionUserId,
  disabled = false,
  onReactionsChange,
  onError,
}: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const [busyCode, setBusyCode] = useState<string | null>(null);
  const items = useMemo(
    () => aggregateMessageReactions(reactions, sessionUserId),
    [reactions, sessionUserId],
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

  if (disabled) return null;

  return (
    <div className="cm-room-thread__message-reactions">
      <CommercialReactionBar
        listAriaLabel={content.reactionsAriaLabel}
        addAriaLabel={content.reactionAddAriaLabel}
        items={items}
        onToggle={(code) => {
          void toggle(code);
        }}
        onAdd={(code) => {
          void toggle(code);
        }}
        emojiAdd={{
          listAriaLabel: content.reactionEmojiMenuAriaLabel,
          portalScopeClassName: CM_PORTAL_SCOPE,
        }}
      />
    </div>
  );
}
