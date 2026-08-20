import catalog from "./emoji-catalog.json";

export type EmojiCatalogItem = {
  id: string;
  glyph: string;
  label: string;
};

type EmojiCatalogFile = {
  emojis: EmojiCatalogItem[];
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

export function getEmojiCatalog(): readonly EmojiCatalogItem[] {
  return EMOJI_CATALOG;
}
