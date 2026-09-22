/** Resize selected `<img>` inside RichTextEditor via width/height attrs (BFF allowlist). */

export const RICH_TEXT_IMAGE_MIN_WIDTH = 48;
export const RICH_TEXT_IMAGE_MAX_WIDTH = 1200;

export type RichTextImageSize = {
  width: number;
  height: number;
};

export function clampRichTextImageWidth(
  width: number,
  options?: { min?: number; max?: number; containerWidth?: number },
): number {
  const min = options?.min ?? RICH_TEXT_IMAGE_MIN_WIDTH;
  let max = options?.max ?? RICH_TEXT_IMAGE_MAX_WIDTH;
  if (options?.containerWidth && options.containerWidth > 0) {
    max = Math.min(max, Math.floor(options.containerWidth));
  }
  if (max < min) return min;
  return Math.max(min, Math.min(max, Math.round(width)));
}

export function resolveRichTextImageNaturalSize(img: HTMLImageElement): RichTextImageSize {
  const naturalW = img.naturalWidth || img.width || img.getBoundingClientRect().width || 320;
  const naturalH = img.naturalHeight || img.height || img.getBoundingClientRect().height || 240;
  return {
    width: Math.max(1, Math.round(naturalW)),
    height: Math.max(1, Math.round(naturalH)),
  };
}

/** Keep aspect ratio; persist via HTML width/height (not CSS — sanitizer strips width style). */
export function applyRichTextImageWidth(
  img: HTMLImageElement,
  nextWidth: number,
  options?: { min?: number; max?: number; containerWidth?: number },
): RichTextImageSize {
  const natural = resolveRichTextImageNaturalSize(img);
  const width = clampRichTextImageWidth(nextWidth, options);
  const height = Math.max(1, Math.round((width * natural.height) / natural.width));
  img.setAttribute("width", String(width));
  img.setAttribute("height", String(height));
  img.style.width = `${width}px`;
  img.style.height = `${height}px`;
  img.style.maxWidth = "100%";
  return { width, height };
}

export function clearRichTextImageInlineSizeStyles(img: HTMLImageElement): void {
  img.style.removeProperty("width");
  img.style.removeProperty("height");
}
