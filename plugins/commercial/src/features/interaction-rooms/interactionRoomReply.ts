import type { InteractionMessageDto } from "../../api/interactionRoomsApi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

const PREVIEW_MAX = 120;

export function truncateReplyPreview(body: string, max = PREVIEW_MAX): string {
  const compact = body.replace(/\s+/g, " ").trim();
  if (compact.length <= max) return compact;
  return `${compact.slice(0, Math.max(0, max - 1)).trimEnd()}…`;
}

export function buildReplyComposerBanner(
  message: InteractionMessageDto | null | undefined,
  authorName: string | null | undefined,
): { label: string; preview?: string } | null {
  if (!message) return null;
  const author = (authorName || "").trim();
  const label = author
    ? INTERACTION_ROOMS_CONTENT.replyToAuthorLabel.replace("{author}", author)
    : INTERACTION_ROOMS_CONTENT.replyToFallbackLabel;
  const preview = truncateReplyPreview(message.body_text || "");
  return preview ? { label, preview } : { label };
}

export function buildEditComposerBanner(
  message: InteractionMessageDto | null | undefined,
): { label: string; preview?: string } | null {
  if (!message) return null;
  const preview = truncateReplyPreview(message.body_text || "");
  return {
    label: INTERACTION_ROOMS_CONTENT.editBannerLabel,
    preview: preview || INTERACTION_ROOMS_CONTENT.editBannerFallbackPreview,
  };
}
