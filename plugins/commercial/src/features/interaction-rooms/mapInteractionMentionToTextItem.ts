import type { MentionTextItem } from "@delpi/plugin-ui/index";

import { profileLinkTitle } from "../../content/entityLinkHints";
import { resolveInteractionEntityHref } from "./resolveInteractionEntityHref";

export type InteractionMentionLike = {
  mention_kind?: string;
  kind?: string;
  label: string;
  ref?: Record<string, unknown> | null;
};

function mentionKind(mention: InteractionMentionLike): string {
  return String(mention.mention_kind ?? mention.kind ?? "").trim();
}

function mentionUserId(ref: Record<string, unknown> | null | undefined): string {
  if (!ref || typeof ref !== "object") return "";
  return String(ref.user_id ?? ref.id ?? "").trim();
}

/**
 * DTO de menção da Sala → item do MentionText (href/avatar para kind=user).
 */
export function mapInteractionMentionToTextItem(
  mention: InteractionMentionLike,
  options: {
    basePath: string;
    photoByUserId?: ReadonlyMap<string, string> | null;
  },
): MentionTextItem {
  const { basePath, photoByUserId } = options;
  const kind = mentionKind(mention) || "unknown";
  const label = String(mention.label || "").trim() || kind;
  const ref =
    mention.ref && typeof mention.ref === "object" && !Array.isArray(mention.ref)
      ? { ...mention.ref }
      : {};

  const item: MentionTextItem = {
    kind,
    label,
    ref,
  };

  if (kind === "user") {
    const userId = mentionUserId(ref);
    const href = resolveInteractionEntityHref(basePath, "user_profile", ref);
    const name = label.replace(/^@/, "").trim() || label;
    if (href) {
      item.href = href;
      item.title = profileLinkTitle(name);
    }
    item.avatarName = name;
    if (userId && photoByUserId) {
      const src = (photoByUserId.get(userId) ?? "").trim();
      if (src) item.avatarSrc = src;
    }
  }

  return item;
}

export function mapInteractionMentionsToTextItems(
  mentions: readonly InteractionMentionLike[],
  options: {
    basePath: string;
    photoByUserId?: ReadonlyMap<string, string> | null;
  },
): MentionTextItem[] {
  return mentions.map((mention) =>
    mapInteractionMentionToTextItem(mention, options),
  );
}
