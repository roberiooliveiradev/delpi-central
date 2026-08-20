import catalog from "./emoji-catalog.json";

export type EmojiCatalogItem = {
  id: string;
  glyph: string;
  label: string;
};

type EmojiCatalogFile = {
  emojis: EmojiCatalogItem[];
  quickReactionIds?: string[];
};

const data = catalog as EmojiCatalogFile;

/** Catálogo curado (~40) para o composer — sem emoji-mart. */
export const EMOJI_CATALOG: readonly EmojiCatalogItem[] = Object.freeze(
  (data.emojis ?? []).map((item) =>
    Object.freeze({
      id: String(item.id ?? "").trim(),
      glyph: String(item.glyph ?? "").trim(),
      label: String(item.label ?? "").trim(),
    }),
  ),
);

const byId = new Map(EMOJI_CATALOG.map((item) => [item.id, item] as const));

const DEFAULT_QUICK_IDS = [
  "thumbs_up",
  "red_heart",
  "joy",
  "eyes",
  "fire",
] as const;

/** Cinco reações rápidas da toolbar (hover) — ids do catálogo. */
export const QUICK_REACTION_CATALOG: readonly EmojiCatalogItem[] = Object.freeze(
  (data.quickReactionIds?.length ? data.quickReactionIds : DEFAULT_QUICK_IDS)
    .map((id) => byId.get(String(id).trim()))
    .filter((item): item is EmojiCatalogItem => Boolean(item)),
);

export function getEmojiCatalog(): readonly EmojiCatalogItem[] {
  return EMOJI_CATALOG;
}

export function getQuickReactionCatalog(): readonly EmojiCatalogItem[] {
  return QUICK_REACTION_CATALOG;
}
