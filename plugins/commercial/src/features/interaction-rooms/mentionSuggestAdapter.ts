import type { MentionMenuHit } from "@delpi/plugin-ui/index";

import type { InteractionMentionSuggestItemDto } from "../../api/interactionRoomsApi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

export type InteractionMentionHit = MentionMenuHit & {
  ref: Record<string, unknown>;
};

export type InteractionMentionPayload = {
  kind: string;
  ref: Record<string, unknown>;
  label: string;
};

function stableRefKey(ref: Record<string, unknown>): string {
  try {
    return JSON.stringify(ref, Object.keys(ref).sort());
  } catch {
    return String(Object.keys(ref).length);
  }
}

export function mentionGroupLabelForKind(kind: string): string {
  const key = kind.trim();
  const map = INTERACTION_ROOMS_CONTENT.mentionKindGroupLabels as Record<
    string,
    string
  >;
  return map[key] ?? INTERACTION_ROOMS_CONTENT.mentionKindGroupFallback;
}

/**
 * DTO da commercial-api → hit do MentionMenu (sem HTTP no kit).
 */
export function mapSuggestItemToMentionHit(
  item: InteractionMentionSuggestItemDto,
  index = 0,
): InteractionMentionHit {
  const kind = String(item.kind || "").trim() || "unknown";
  const label = String(item.label || "").trim() || kind;
  const ref =
    item.ref && typeof item.ref === "object" && !Array.isArray(item.ref)
      ? { ...item.ref }
      : {};
  const id =
    String(item.id || "").trim() ||
    `${kind}:${stableRefKey(ref)}:${label}:${index}`;

  return {
    id,
    kind,
    label,
    subtitle: item.subtitle ? String(item.subtitle) : undefined,
    groupLabel: mentionGroupLabelForKind(kind),
    ref,
    ...(kind === "user"
      ? {
          avatarName: label.replace(/^@/, "").trim() || label,
        }
      : {}),
  };
}

/** Anexa foto resolvida pelo host (blob/CDN) nos hits de usuário. */
export function enrichMentionHitsWithAvatars(
  hits: readonly InteractionMentionHit[],
  photoByUserId?: ReadonlyMap<string, string> | null,
): InteractionMentionHit[] {
  if (!photoByUserId || photoByUserId.size === 0) {
    return [...hits];
  }
  return hits.map((hit) => {
    if (hit.kind !== "user") return hit;
    const userId = String(hit.ref.user_id ?? hit.ref.id ?? "").trim();
    if (!userId) return hit;
    const src = (photoByUserId.get(userId) ?? "").trim();
    if (!src) return hit;
    return { ...hit, avatarSrc: src };
  });
}

export function mapSuggestItemsToMentionHits(
  items: readonly InteractionMentionSuggestItemDto[],
): InteractionMentionHit[] {
  return items.map((item, index) => mapSuggestItemToMentionHit(item, index));
}

export function mentionHitToPayload(
  hit: InteractionMentionHit,
): InteractionMentionPayload {
  return {
    kind: hit.kind,
    ref: { ...hit.ref },
    label: hit.label,
  };
}

/** Mentions cujo rótulo ainda aparece no corpo (após edições no textarea). */
export function mentionsPresentInBody(
  body: string,
  pending: readonly InteractionMentionPayload[],
): InteractionMentionPayload[] {
  const text = body || "";
  const seen = new Set<string>();
  const out: InteractionMentionPayload[] = [];
  for (const mention of pending) {
    const label = mention.label.trim();
    if (!label) continue;
    const token = label.startsWith("@") ? label : `@${label}`;
    if (!text.includes(token) && !text.includes(label)) continue;
    const key = `${mention.kind}:${stableRefKey(mention.ref)}:${label}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(mention);
  }
  return out;
}
