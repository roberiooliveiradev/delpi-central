import { getEmojiCatalog } from "@delpi/plugin-ui/index";

import type { InteractionReactionDto } from "../../api/interactionRoomsApi";

export type AggregatedReaction = {
  code: string;
  label: string;
  count: number;
  reactedByMe?: boolean;
};

const catalogById = new Map(
  getEmojiCatalog().map((item) => [item.id, item] as const),
);

export function reactionLabelForCode(code: string): string {
  const key = code.trim();
  if (!key) return "";
  const fromCatalog = catalogById.get(key);
  if (fromCatalog?.glyph) return fromCatalog.glyph;
  return key;
}

export function aggregateMessageReactions(
  reactions: readonly InteractionReactionDto[] | null | undefined,
  sessionUserId: string | null | undefined,
): AggregatedReaction[] {
  const me = (sessionUserId || "").trim();
  const counts = new Map<string, { count: number; reactedByMe: boolean }>();
  for (const row of reactions ?? []) {
    const code = String(row.code || "").trim();
    if (!code) continue;
    const current = counts.get(code) ?? { count: 0, reactedByMe: false };
    current.count += 1;
    if (me && String(row.user_id || "").trim() === me) {
      current.reactedByMe = true;
    }
    counts.set(code, current);
  }
  return [...counts.entries()]
    .map(([code, value]) => ({
      code,
      label: reactionLabelForCode(code),
      count: value.count,
      reactedByMe: value.reactedByMe,
    }))
    .sort((a, b) => a.code.localeCompare(b.code));
}

export function applyLocalReactionToggle(
  reactions: readonly InteractionReactionDto[],
  options: {
    messageId: string;
    userId: string;
    code: string;
    nextActive: boolean;
  },
): InteractionReactionDto[] {
  const messageId = options.messageId.trim();
  const userId = options.userId.trim();
  const code = options.code.trim();
  if (!messageId || !userId || !code) return [...reactions];
  if (!options.nextActive) {
    return reactions.filter(
      (row) =>
        !(
          String(row.user_id || "").trim() === userId &&
          String(row.code || "").trim() === code
        ),
    );
  }
  // Uma reação por pessoa: ao ativar outro emoji, remove as anteriores do user.
  const withoutMine = reactions.filter(
    (row) => String(row.user_id || "").trim() !== userId,
  );
  return [
    ...withoutMine,
    {
      message_id: messageId,
      user_id: userId,
      code,
    },
  ];
}
