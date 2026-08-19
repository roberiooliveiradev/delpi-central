/** Tamanhos do composer da sala — não reusa a faixa 10–72 do editor de deck. */
export const COMPOSER_FONT_SIZE_MIN = 12;
export const COMPOSER_FONT_SIZE_MAX = 20;
export const COMPOSER_FONT_SIZE_STEP = 2;
export const COMPOSER_FONT_SIZE_DEFAULT = 16;
export const COMPOSER_FONT_SIZE_PRESETS: readonly number[] = [12, 14, 16, 18, 20];

export function clampComposerFontSize(value: number): number {
  return Math.min(
    COMPOSER_FONT_SIZE_MAX,
    Math.max(COMPOSER_FONT_SIZE_MIN, Math.round(value)),
  );
}
