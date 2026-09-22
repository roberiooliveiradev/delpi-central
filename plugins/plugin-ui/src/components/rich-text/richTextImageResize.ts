/** Resize selected `<img>` inside RichTextEditor via width/height attrs (BFF allowlist ≤4096). */

export const RICH_TEXT_IMAGE_MIN_WIDTH = 48;
/** Align with helpdesk-api / BFF img width allowlist. */
export const RICH_TEXT_IMAGE_MAX_WIDTH = 4096;
/** Compose paste: fit into the editor column (author can still enlarge past this). */
export const RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH = 720;

export type RichTextImageSize = {
  width: number;
  height: number;
};

export function clampRichTextImageWidth(
  width: number,
  options?: { min?: number; max?: number; containerWidth?: number },
): number {
  const min = options?.min ?? RICH_TEXT_IMAGE_MIN_WIDTH;
  // Resize may exceed the column (editor scrolls). Do not clamp to containerWidth here.
  const max = options?.max ?? RICH_TEXT_IMAGE_MAX_WIDTH;
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

/** True when src is the compose loading placeholder (must never drive fit/resize). */
export function isRichTextImagePlaceholderSrc(src: string | null | undefined): boolean {
  const value = String(src || "").trim();
  return value.startsWith("data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP");
}

/**
 * Keep aspect ratio; persist via HTML width/height (sanitizer strips width style).
 * - fit (default): width attr + width style, height auto, max-width 100% so the column can shrink.
 * - lockHeight: enlarge handle — fixed px box, may exceed column (editor scrolls).
 */
export function applyRichTextImageWidth(
  img: HTMLImageElement,
  nextWidth: number,
  options?: { min?: number; max?: number; containerWidth?: number; lockHeight?: boolean },
): RichTextImageSize {
  const natural = resolveRichTextImageNaturalSize(img);
  const width = clampRichTextImageWidth(nextWidth, options);
  const height = Math.max(1, Math.round((width * natural.height) / natural.width));
  img.setAttribute("width", String(width));
  img.setAttribute("height", String(height));
  img.style.width = `${width}px`;
  if (options?.lockHeight) {
    img.style.height = `${height}px`;
    img.style.maxWidth = "none";
  } else {
    img.style.height = "auto";
    img.style.maxWidth = "100%";
  }
  return { width, height };
}

/**
 * On paste/attach: fit into the editor column so writing stays usable.
 * Enlarge via handle can still go up to RICH_TEXT_IMAGE_MAX_WIDTH.
 * Skips placeholder / unloaded images so a 1×1 GIF never locks width=48.
 */
export function fitRichTextImageToContainer(
  img: HTMLImageElement,
  containerWidth: number,
  options?: { defaultMaxWidth?: number; maxWidth?: number },
): RichTextImageSize | null {
  if (img.getAttribute("width")) return null;
  if (isRichTextImagePlaceholderSrc(img.getAttribute("src") || img.src)) return null;
  if (img.naturalWidth > 0 && img.naturalWidth <= 1 && img.naturalHeight <= 1) return null;
  const natural = resolveRichTextImageNaturalSize(img);
  if (natural.width <= 1) return null;
  const column = Math.max(
    RICH_TEXT_IMAGE_MIN_WIDTH,
    Math.floor((containerWidth > 0 ? containerWidth : RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH) * 0.92),
  );
  const softMax = options?.defaultMaxWidth ?? RICH_TEXT_IMAGE_DEFAULT_MAX_WIDTH;
  const hardMax = options?.maxWidth ?? RICH_TEXT_IMAGE_MAX_WIDTH;
  const target = Math.min(natural.width, column, softMax, hardMax);
  return applyRichTextImageWidth(img, target, { max: hardMax, lockHeight: false });
}

export function clearRichTextImageInlineSizeStyles(img: HTMLImageElement): void {
  img.style.removeProperty("width");
  img.style.removeProperty("height");
  img.style.removeProperty("max-width");
}

/** After blob replace: drop sizes that were never author-chosen so fit can re-run. */
export function clearRichTextImageSizeForRefit(img: HTMLImageElement): void {
  img.removeAttribute("width");
  img.removeAttribute("height");
  clearRichTextImageInlineSizeStyles(img);
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
