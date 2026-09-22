/** Resize selected `<img>` inside RichTextEditor via width/height attrs (BFF allowlist). */

export const RICH_TEXT_IMAGE_MIN_WIDTH = 48;
export const RICH_TEXT_IMAGE_MAX_WIDTH = 1200;
/** Default compose width when the image has no width yet (paste/attach). */
export const RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH = 520;

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

/**
 * Fit oversized images into the editor on insert (paste/attach) when no width attr yet.
 * No-op if the author already chose width/height.
 */
export function fitRichTextImageToContainer(
  img: HTMLImageElement,
  containerWidth: number,
  options?: { defaultMaxWidth?: number },
): RichTextImageSize | null {
  if (img.getAttribute("width")) return null;
  const natural = resolveRichTextImageNaturalSize(img);
  const budget = Math.max(
    RICH_TEXT_IMAGE_MIN_WIDTH,
    Math.floor((containerWidth > 0 ? containerWidth : RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH) * 0.92),
  );
  const defaultMax = options?.defaultMaxWidth ?? RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH;
  const target = Math.min(natural.width, budget, defaultMax);
  if (target >= natural.width && natural.width <= budget) {
    // Still stamp attrs so resize/sanitizer stay stable.
    return applyRichTextImageWidth(img, natural.width, { containerWidth: budget });
  }
  return applyRichTextImageWidth(img, target, { containerWidth: budget });
}

export function clearRichTextImageInlineSizeStyles(img: HTMLImageElement): void {
  img.style.removeProperty("width");
  img.style.removeProperty("height");
}

/** SE handle position relative to `root`, clamped to the visible image∩editor box. */
export function resolveRichTextImageResizeHandlePosition(args: {
  img: HTMLImageElement;
  root: HTMLElement;
  editor: HTMLElement;
  handleSize?: number;
}): { top: number; left: number; width: number; height: number } {
  const handleSize = args.handleSize ?? 12;
  const rootRect = args.root.getBoundingClientRect();
  const imgRect = args.img.getBoundingClientRect();
  const editorRect = args.editor.getBoundingClientRect();
  const visibleLeft = Math.max(imgRect.left, editorRect.left);
  const visibleTop = Math.max(imgRect.top, editorRect.top);
  const visibleRight = Math.min(imgRect.right, editorRect.right);
  const visibleBottom = Math.min(imgRect.bottom, editorRect.bottom);
  const width = Math.max(handleSize, visibleRight - visibleLeft);
  const height = Math.max(handleSize, visibleBottom - visibleTop);
  return {
    top: visibleBottom - rootRect.top - handleSize / 2,
    left: visibleRight - rootRect.left - handleSize / 2,
    width,
    height,
  };
}
