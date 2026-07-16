export type RichTextFontOption = {
  value: string;
  label: string;
};

/** Famílias alinhadas ao catálogo do tv-dashboard (system fonts). */
export const RICH_TEXT_FONT_FAMILIES: readonly RichTextFontOption[] = [
  { value: "Inter, system-ui, sans-serif", label: "Inter" },
  { value: "Arial, Helvetica, sans-serif", label: "Arial" },
  { value: "Georgia, serif", label: "Georgia" },
  { value: "Times New Roman, Times, serif", label: "Times New Roman" },
  { value: "Courier New, Courier, monospace", label: "Courier New" },
] as const;

export const RICH_TEXT_FONT_SIZE_MIN = 10;
export const RICH_TEXT_FONT_SIZE_MAX = 72;
export const RICH_TEXT_FONT_SIZE_STEP = 1;
export const RICH_TEXT_FONT_SIZE_DEFAULT = 16;
export const RICH_TEXT_FONT_SIZE_PRESETS: readonly number[] = [
  12, 14, 16, 18, 20, 24, 28, 32, 40, 48,
] as const;

export function clampRichTextFontSize(value: number): number {
  return Math.min(RICH_TEXT_FONT_SIZE_MAX, Math.max(RICH_TEXT_FONT_SIZE_MIN, Math.round(value)));
}
