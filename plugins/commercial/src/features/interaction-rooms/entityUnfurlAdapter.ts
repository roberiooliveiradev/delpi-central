import type { EntityUnfurlField } from "@delpi/plugin-ui/index";

import type { InteractionEntityPreviewDto } from "../../api/interactionRoomsApi";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";
import { mentionGroupLabelForKind } from "./mentionSuggestAdapter";

export type EntityUnfurlCardModel = {
  title: string;
  kindLabel: string;
  accessible: boolean;
  deniedLabel: string;
  openLabel: string;
  fields: EntityUnfurlField[];
  hrefStrategy: string;
  ref: Record<string, unknown>;
};

function fieldLabelForKey(key: string): string {
  const map = INTERACTION_ROOMS_CONTENT.unfurlFieldLabels as Record<string, string>;
  return map[key] ?? key;
}

function fieldsFromPreview(
  fields: Record<string, unknown> | undefined,
  subtitle: string | undefined,
): EntityUnfurlField[] {
  const out: EntityUnfurlField[] = [];
  if (subtitle?.trim()) {
    out.push({
      id: "subtitle",
      label: INTERACTION_ROOMS_CONTENT.unfurlSubtitleFieldLabel,
      value: subtitle.trim(),
    });
  }
  for (const [key, raw] of Object.entries(fields ?? {})) {
    if (raw == null) continue;
    const value = typeof raw === "string" ? raw.trim() : String(raw);
    if (!value) continue;
    out.push({
      id: key,
      label: fieldLabelForKey(key),
      value,
    });
  }
  return out;
}

/**
 * DTO de entity-preview → modelo do EntityUnfurlCard (kit sem if por kind).
 */
export function mapPreviewToUnfurlCardModel(
  preview: InteractionEntityPreviewDto,
): EntityUnfurlCardModel {
  const accessible = Boolean(preview.accessible);
  const kind = String(preview.kind || "").trim() || "unknown";
  return {
    title: accessible
      ? String(preview.label || "").trim() || kind
      : INTERACTION_ROOMS_CONTENT.unfurlDeniedTitle,
    kindLabel: mentionGroupLabelForKind(kind),
    accessible,
    deniedLabel: INTERACTION_ROOMS_CONTENT.unfurlDeniedLabel,
    openLabel: INTERACTION_ROOMS_CONTENT.unfurlOpenLabel,
    fields: accessible
      ? fieldsFromPreview(preview.fields, preview.subtitle)
      : [],
    hrefStrategy: String(preview.hrefStrategy || "").trim(),
    ref:
      preview.ref && typeof preview.ref === "object" && !Array.isArray(preview.ref)
        ? { ...preview.ref }
        : {},
  };
}

export function shouldUnfurlMentionKind(kind: string): boolean {
  const id = kind.trim().toLowerCase();
  if (!id) return false;
  return (INTERACTION_ROOMS_CONTENT.unfurlPreviewKinds as readonly string[]).includes(
    id,
  );
}
